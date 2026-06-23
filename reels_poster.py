"""
reels_poster.py
---------------
Runs inside GitHub Actions on a cron schedule.
Reads reels_schedule.json, finds a reel due within ±25 min of NOW,
and posts it to Instagram using media_type=REELS.

Videos are served from GitHub raw URLs (must be under 100MB and committed to repo).
For videos over 100MB, compress with: ffmpeg -i input.mov -vcodec h264 -acodec aac -b:v 4M output.mp4

GitHub Secrets required:
  PAGE_TOKEN  — Amy's long-lived Facebook Page token
  IG_ID       — Instagram Business Account ID
  REPO_OWNER  — e.g. stabiliti
  REPO_NAME   — e.g. FBIGAMY

Usage:
  python reels_poster.py                    # normal run
  python reels_poster.py --post 2           # force-post reel #2
  python reels_poster.py --dry-run          # preview without posting
"""
import os, json, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────────────────────────
PAGE_TOKEN  = os.environ.get("PAGE_TOKEN") or (
    open("page_token.txt").read().strip() if os.path.exists("page_token.txt") else None
)
IG_ID       = os.environ.get("IG_ID", "17841455628778748")
REPO_OWNER  = os.environ.get("REPO_OWNER", "stabiliti")
REPO_NAME   = os.environ.get("REPO_NAME", "FBIGAMY")
REPO_BRANCH = "main"
BASE        = "https://graph.facebook.com/v25.0"
GITHUB_RAW  = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}"
SCHEDULE_FILE = "reels_schedule.json"
STATE_FILE    = "reels_state.json"
WINDOW_MIN    = 30        # ± minutes (reels get a slightly larger window)
POLL_MAX      = 300       # 5 min max — video processing takes longer than images
POLL_INTERVAL = 10
DRY_RUN       = "--dry-run" in sys.argv

if not PAGE_TOKEN:
    print("ERROR: PAGE_TOKEN not set.")
    sys.exit(1)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def api_get(path, params=None):
    p = {"access_token": PAGE_TOKEN}
    if params:
        p.update(params)
    url = f"{BASE}/{path}?{urllib.parse.urlencode(p)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def api_post(path, data):
    data["access_token"] = PAGE_TOKEN
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def load_state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w"), indent=2)

def wait_for_reel_container(container_id):
    """Poll until reel container is FINISHED. Videos take longer than images."""
    deadline = time.time() + POLL_MAX
    attempts = 0
    while time.time() < deadline:
        r = api_get(container_id, {"fields": "status_code,status"})
        status = r.get("status_code", r.get("status", "UNKNOWN"))
        attempts += 1
        if status == "FINISHED":
            print(f"  ✓ Container ready after {attempts * POLL_INTERVAL}s")
            return True
        if status in ("ERROR", "EXPIRED"):
            print(f"  ✗ Container error: {status} — {r}")
            return False
        if attempts % 3 == 0:
            print(f"  … Processing reel ({attempts * POLL_INTERVAL}s)… status={status}")
        time.sleep(POLL_INTERVAL)
    print(f"  ✗ Timed out after {POLL_MAX}s waiting for reel processing")
    return False

# ── REEL POSTING ──────────────────────────────────────────────────────────────
def post_reel(entry):
    filename  = entry["filename"]
    caption   = entry["caption"]
    reel_num  = entry["reel_num"]
    video_url = f"{GITHUB_RAW}/content/reels/{filename}"

    print(f"\n  Posting reel #{reel_num}: {filename}")
    print(f"  URL: {video_url}")

    if DRY_RUN:
        print(f"  [DRY RUN] Would post reel with caption: {caption[:60]}...")
        return "dry_run_id"

    # Step 1 — create reel container
    params = {
        "media_type":    "REELS",
        "video_url":     video_url,
        "caption":       caption,
        "share_to_feed": "true",
    }
    # Add cover image if specified
    if entry.get("cover_image_url"):
        params["cover_url"] = entry["cover_image_url"]

    res = api_post(f"{IG_ID}/media", params)
    if "id" not in res:
        err = res.get("error", {}).get("message", str(res))
        print(f"  ✗ Container failed: {err}")
        return None
    container_id = res["id"]
    print(f"  ✓ container_id={container_id}")

    # Step 2 — wait for video processing (takes 30-120s typically)
    print(f"  Processing video (this takes up to {POLL_MAX}s)…")
    if not wait_for_reel_container(container_id):
        return None

    # Step 3 — publish
    pub = api_post(f"{IG_ID}/media_publish", {"creation_id": container_id})
    if "id" not in pub:
        err = pub.get("error", {}).get("message", str(pub))
        print(f"  ✗ Publish failed: {err}")
        return None

    media_id = pub["id"]
    print(f"  ✓ Reel published! media_id={media_id}")
    return media_id

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    now   = datetime.now(timezone.utc)
    state = load_state()

    if not os.path.exists(SCHEDULE_FILE):
        print(f"ERROR: {SCHEDULE_FILE} not found.")
        sys.exit(1)
    sched = json.load(open(SCHEDULE_FILE))

    print(f"Reels Poster — {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    if DRY_RUN:
        print("DRY RUN MODE")

    force_num = None
    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        force_num = int(sys.argv[idx + 1])

    posted_any = False
    for entry in sched:
        reel_num = entry["reel_num"]

        if state.get(str(reel_num)) == "posted" and not force_num:
            continue
        if force_num and reel_num != force_num:
            continue

        slot  = datetime.fromisoformat(entry["scheduled_utc"].replace("Z", "+00:00"))
        delta = abs((now - slot).total_seconds() / 60)

        if force_num or delta <= WINDOW_MIN:
            print(f"\n{'='*55}")
            print(f"Reel #{reel_num} — {entry['filename']}")
            print(f"Scheduled: {slot.strftime('%Y-%m-%d %H:%M UTC')} | Δ={delta:.1f} min")

            media_id = post_reel(entry)
            if media_id or DRY_RUN:
                state[str(reel_num)] = "posted"
                save_state(state)
                posted_any = True
                print(f"\n✓ Reel #{reel_num} complete.")
            break
        else:
            slot_str = slot.strftime('%Y-%m-%d %H:%M UTC')
            print(f"No reel due at {now.strftime('%H:%M UTC')} "
                  f"(next: #{reel_num} at {slot_str})")
            break

    if not posted_any and not force_num:
        print(f"\nNo reel due at {now.strftime('%Y-%m-%d %H:%M UTC')} ± {WINDOW_MIN} min.")

if __name__ == "__main__":
    main()

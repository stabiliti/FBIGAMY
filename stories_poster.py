"""
stories_poster.py
-----------------
Runs inside GitHub Actions on a cron schedule.
Reads stories_schedule.json, finds any stories due within ±25 min of NOW,
and posts them to Instagram using media_type=STORIES.

Images are served from GitHub raw URLs.

GitHub Secrets required:
  PAGE_TOKEN  — Amy's long-lived Facebook Page token
  IG_ID       — Instagram Business Account ID
  REPO_OWNER  — e.g. stabiliti
  REPO_NAME   — e.g. FBIGAMY

Usage:
  python stories_poster.py                   # normal run
  python stories_poster.py --post 5          # force-post story #5
  python stories_poster.py --dry-run         # preview without posting
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
SCHEDULE_FILE = "stories_schedule.json"
STATE_FILE    = "stories_state.json"
WINDOW_MIN    = 25
POLL_MAX      = 60
DRY_RUN       = "--dry-run" in sys.argv

if not PAGE_TOKEN:
    print("ERROR: PAGE_TOKEN not set.")
    sys.exit(1)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def api_post(path, data):
    data["access_token"] = PAGE_TOKEN
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

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

def load_state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w"), indent=2)

def wait_for_container(container_id):
    deadline = time.time() + POLL_MAX
    while time.time() < deadline:
        r = api_get(container_id, {"fields": "status_code,status"})
        status = r.get("status_code", r.get("status", "UNKNOWN"))
        if status == "FINISHED":
            return True
        if status in ("ERROR", "EXPIRED"):
            print(f"  ✗ Container error: {status}")
            return False
        print(f"  … status: {status}, waiting 5s")
        time.sleep(5)
    print(f"  ✗ Timed out waiting for container")
    return False

# ── STORY POSTING ─────────────────────────────────────────────────────────────
def post_story(entry):
    filename   = entry["filename"]
    story_num  = entry["story_num"]
    image_url  = f"{GITHUB_RAW}/content/stories/{filename}"

    print(f"\n  Posting story #{story_num}: {filename}")
    print(f"  URL: {image_url}")

    if DRY_RUN:
        print(f"  [DRY RUN] Would post story")
        return "dry_run_id"

    # Step 1 — create story container
    res = api_post(f"{IG_ID}/media", {
        "image_url":  image_url,
        "media_type": "STORIES",
    })
    if "id" not in res:
        err = res.get("error", {}).get("message", str(res))
        print(f"  ✗ Container failed: {err}")
        return None
    container_id = res["id"]
    print(f"  ✓ container_id={container_id}")

    # Step 2 — wait for FINISHED
    print(f"  Waiting for processing…")
    if not wait_for_container(container_id):
        return None

    # Step 3 — publish
    pub = api_post(f"{IG_ID}/media_publish", {"creation_id": container_id})
    if "id" not in pub:
        err = pub.get("error", {}).get("message", str(pub))
        print(f"  ✗ Publish failed: {err}")
        return None

    media_id = pub["id"]
    print(f"  ✓ Published! media_id={media_id}")
    return media_id

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    now    = datetime.now(timezone.utc)
    sched  = json.load(open(SCHEDULE_FILE)) if os.path.exists(SCHEDULE_FILE) else []
    state  = load_state()

    print(f"Stories Poster — {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    if DRY_RUN:
        print("DRY RUN MODE")

    force_num = None
    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        force_num = int(sys.argv[idx + 1])

    posted = 0
    for entry in sched:
        story_num = entry["story_num"]

        if state.get(str(story_num)) == "posted" and not force_num:
            continue

        if force_num and story_num != force_num:
            continue

        slot  = datetime.fromisoformat(entry["scheduled_utc"].replace("Z", "+00:00"))
        delta = abs((now - slot).total_seconds() / 60)

        if force_num or delta <= WINDOW_MIN:
            media_id = post_story(entry)
            if media_id or DRY_RUN:
                state[str(story_num)] = "posted"
                posted += 1
            if force_num:
                break
        else:
            if posted == 0:
                # Haven't started yet — check if this slot is upcoming
                remaining = (slot - now).total_seconds() / 60
                if remaining > WINDOW_MIN:
                    print(f"No story due now. Next: #{story_num} at {slot.strftime('%H:%M UTC')} "
                          f"({remaining:.0f} min away)")
                    break

    save_state(state)

    if posted:
        print(f"\n✓ Done — posted {posted} story/stories this run.")
    elif not force_num:
        print(f"No stories due at {now.strftime('%Y-%m-%d %H:%M UTC')} ± {WINDOW_MIN} min.")

if __name__ == "__main__":
    main()

"""
carousel_poster.py
------------------
Runs inside GitHub Actions on a cron schedule.
Reads carousel_schedule.json, finds a carousel due within ±25 min of NOW,
posts it to Instagram as a multi-image Carousel using the Content Publishing API.

Images are served from GitHub raw URLs — no external hosting needed.

GitHub Secrets required:
  PAGE_TOKEN  — Amy's long-lived Facebook Page token
  IG_ID       — Instagram Business Account ID
  REPO_OWNER  — e.g. stabiliti
  REPO_NAME   — e.g. FBIGAMY

Usage:
  python carousel_poster.py                  # normal run
  python carousel_poster.py --post 3         # force-post carousel #3
  python carousel_poster.py --dry-run        # show what would post, don't post
"""
import os, json, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

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
SCHEDULE_FILE = "carousel_schedule.json"
STATE_FILE    = "carousel_state.json"
WINDOW_MIN    = 25       # ± minutes around scheduled time
POLL_MAX      = 60       # max seconds to poll container status
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

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        print(f"ERROR: {SCHEDULE_FILE} not found.")
        sys.exit(1)
    return json.load(open(SCHEDULE_FILE))

def image_url(folder, slide_num, slide_count):
    """Build GitHub raw URL for a carousel slide."""
    return f"{GITHUB_RAW}/content/carousels/{folder}/slide_{slide_num:02d}.png"

def wait_for_container(container_id, label="container"):
    """Poll until container status is FINISHED or error out."""
    deadline = time.time() + POLL_MAX
    while time.time() < deadline:
        r = api_get(container_id, {"fields": "status_code,status"})
        status = r.get("status_code", r.get("status", "UNKNOWN"))
        if status == "FINISHED":
            return True
        if status in ("ERROR", "EXPIRED"):
            print(f"  ✗ {label} status: {status} — {r}")
            return False
        print(f"  … {label} status: {status}, waiting 5s")
        time.sleep(5)
    print(f"  ✗ Timed out waiting for {label}")
    return False

# ── CAROUSEL POSTING ──────────────────────────────────────────────────────────
def post_carousel(entry):
    folder      = entry["carousel_folder"]
    slide_count = entry["slide_count"]
    caption     = entry["caption"]
    post_num    = entry["post_num"]

    print(f"\nPosting carousel #{post_num}: {folder} ({slide_count} slides)")

    if DRY_RUN:
        print(f"  [DRY RUN] Would post {slide_count} slides from {folder}")
        for i in range(1, slide_count + 1):
            print(f"    slide {i}: {image_url(folder, i, slide_count)}")
        return None

    # Step 1 — create child image containers
    child_ids = []
    for i in range(1, slide_count + 1):
        url = image_url(folder, i, slide_count)
        print(f"  Creating child {i}/{slide_count}: {url.split('/')[-1]}")
        res = api_post(f"{IG_ID}/media", {
            "image_url": url,
            "is_carousel_item": "true",
        })
        if "id" not in res:
            print(f"  ✗ Child {i} failed: {res.get('error', {}).get('message', str(res))}")
            return None
        child_ids.append(res["id"])
        print(f"    ✓ child_id={res['id']}")

    # Step 2 — create parent carousel container
    print(f"\n  Creating carousel container ({len(child_ids)} children)…")
    res = api_post(f"{IG_ID}/media", {
        "media_type":  "CAROUSEL",
        "children":    ",".join(child_ids),
        "caption":     caption,
    })
    if "id" not in res:
        print(f"  ✗ Carousel container failed: {res.get('error', {}).get('message', str(res))}")
        return None
    carousel_id = res["id"]
    print(f"  ✓ carousel_container_id={carousel_id}")

    # Step 3 — wait for FINISHED
    print(f"  Waiting for container to finish processing…")
    if not wait_for_container(carousel_id, "carousel"):
        return None

    # Step 4 — publish
    print(f"  Publishing…")
    pub = api_post(f"{IG_ID}/media_publish", {"creation_id": carousel_id})
    if "id" not in pub:
        print(f"  ✗ Publish failed: {pub.get('error', {}).get('message', str(pub))}")
        return None

    media_id = pub["id"]
    print(f"  ✓ Published! media_id={media_id}")
    return media_id

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    now     = datetime.now(timezone.utc)
    sched   = load_schedule()
    state   = load_state()

    print(f"Carousel Poster — {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    if DRY_RUN:
        print("DRY RUN MODE — no posts will be made")

    # Force-post mode
    force_num = None
    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        force_num = int(sys.argv[idx + 1])

    # ── Force-post a specific carousel ───────────────────────────────────────
    if force_num:
        entry = next((e for e in sched if e["post_num"] == force_num), None)
        if not entry:
            print(f"Carousel #{force_num} not found in schedule.")
            return
        print(f"\n{'='*55}")
        print(f"Carousel #{force_num} — {entry['carousel_folder']} [FORCED]")
        media_id = post_carousel(entry)
        if media_id or DRY_RUN:
            state[str(force_num)] = "posted"
            save_state(state)
            print(f"\n✓ Carousel #{force_num} complete.")
        return

    # ── Normal run: post the next unposted carousel ───────────────────────────
    # No time-matching — GitHub crons drift. Just post next in sequence.
    next_entry = next(
        (e for e in sched if state.get(str(e["post_num"])) != "posted"),
        None
    )

    if not next_entry:
        print("✓ All carousels have been posted!")
        return

    post_num = next_entry["post_num"]
    total    = len(sched)
    print(f"\n{'='*55}")
    print(f"Next unposted: Carousel #{post_num} of {total} — {next_entry['carousel_folder']}")

    media_id = post_carousel(next_entry)
    if media_id or DRY_RUN:
        state[str(post_num)] = "posted"
        save_state(state)
        remaining = sum(1 for e in sched if state.get(str(e["post_num"])) != "posted") - 1
        print(f"\n✓ Carousel #{post_num} complete. {remaining} remaining.")
    else:
        print(f"\n✗ Failed to post carousel #{post_num}.")

if __name__ == "__main__":
    main()

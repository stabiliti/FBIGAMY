"""
ig_poster.py
------------
Runs inside GitHub Actions at each scheduled time slot.
Reads ig_schedule.json, finds the post due RIGHT NOW, and publishes
it immediately to Instagram via the Content Publishing API.

Immediate publishing does NOT require Meta's scheduling whitelist.

Environment variables (set as GitHub Secrets):
  PAGE_TOKEN   — Amy's long-lived Facebook Page token
  IG_ID        — Instagram Business Account ID

The image files must be in atomic_summer_images/ in the same repo.
GitHub raw URLs are used so IG can fetch the image directly.
"""
import os, json, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────────────────────────
PAGE_TOKEN   = os.environ["PAGE_TOKEN"]
IG_ID        = os.environ["IG_ID"]
REPO_OWNER   = os.environ["REPO_OWNER"]
REPO_NAME    = os.environ["REPO_NAME"]
BASE         = "https://graph.facebook.com/v25.0"
WINDOW_MIN   = 25   # ± minutes around slot time (GitHub cron can drift a few mins)
SCHEDULE_FILE = "ig_schedule.json"

# ── LOAD SCHEDULE ─────────────────────────────────────────────────────────────
def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        print(f"ERROR: {SCHEDULE_FILE} not found in repo root.")
        sys.exit(1)
    with open(SCHEDULE_FILE, encoding="utf-8") as f:
        return json.load(f)

# ── FIND DUE POST ─────────────────────────────────────────────────────────────
def find_due_post(schedule):
    now = datetime.now(timezone.utc)
    print(f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    for post in schedule:
        if post.get("is_video"):
            continue  # Videos need manual upload — skip
        post_time = datetime.fromisoformat(post["scheduled_utc"].replace("Z", "+00:00"))
        diff_min  = (now - post_time).total_seconds() / 60
        if -WINDOW_MIN <= diff_min <= WINDOW_MIN:
            print(f"Found due post: #{post['post_num']} scheduled at {post['scheduled_utc']} (diff: {diff_min:.1f} min)")
            return post
    return None

# ── POST TO INSTAGRAM ─────────────────────────────────────────────────────────
def post_to_ig(caption, image_url):
    print(f"Image URL: {image_url}")

    # Step 1 — Create media container
    container_data = {
        "image_url":    image_url,
        "caption":      caption,
        "access_token": PAGE_TOKEN,
    }
    payload = urllib.parse.urlencode(container_data).encode()
    req     = urllib.request.Request(f"{BASE}/{IG_ID}/media", data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            container_id = json.loads(r.read()).get("id")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"IG container error: {err.get('error', {}).get('message', str(err))}")
        return False

    if not container_id:
        print("No container ID returned from IG.")
        return False
    print(f"Container created: {container_id}")

    # Step 2 — Publish immediately
    pub_data    = {"creation_id": container_id, "access_token": PAGE_TOKEN}
    pub_payload = urllib.parse.urlencode(pub_data).encode()
    pub_req     = urllib.request.Request(f"{BASE}/{IG_ID}/media_publish", data=pub_payload, method="POST")
    try:
        with urllib.request.urlopen(pub_req, timeout=30) as r:
            result     = json.loads(r.read())
            ig_post_id = result.get("id")
            if ig_post_id:
                print(f"✓ Posted to Instagram: {ig_post_id}")
                return True
            else:
                print(f"Unexpected publish response: {result}")
                return False
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"IG publish error: {err.get('error', {}).get('message', str(err))}")
        return False

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    schedule = load_schedule()
    post     = find_due_post(schedule)

    if not post:
        now = datetime.now(timezone.utc)
        print(f"No post due at {now.strftime('%Y-%m-%d %H:%M')} UTC (±{WINDOW_MIN} min). Nothing to do.")
        sys.exit(0)

    print(f"\nPosting: #{post['post_num']} — {post['label']}")
    print(f"Caption preview: {post['caption'][:80]}...")

    # Build public GitHub raw URL for the image
    filename  = urllib.parse.quote(post["image_filename"])
    image_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/atomic_summer_images/{filename}"

    success = post_to_ig(post["caption"], image_url)
    sys.exit(0 if success else 1)

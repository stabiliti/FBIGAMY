"""
comment_watcher.py
------------------
Watches Facebook page posts AND Instagram posts for new comments.
When a keyword is detected in a comment, automatically sends the commenter
a private DM with the relevant response.

Facebook:  uses POST /{comment-id}/private_replies  (no prior DM needed)
Instagram: uses POST /{ig-user-id}/messages to the commenter's IGSID

Run:  py comment_watcher.py
Runs forever, checks every 30 minutes. Press Ctrl+C to stop.
"""
import urllib.request, urllib.error, json, urllib.parse, os, sys, time
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
PAGE_TOKEN = open("page_token.txt").read().strip() if os.path.exists("page_token.txt") else "PASTE_PAGE_TOKEN_HERE"
PAGE_ID    = "224952947543823"
IG_ID      = open("ig_id.txt").read().strip() if os.path.exists("ig_id.txt") else "17841455628778748"
BASE       = "https://graph.facebook.com/v25.0"
STATE_FILE = "comment_state.json"   # tracks comment IDs already handled
POSTS_TO_CHECK = 10                 # how many recent posts to scan on each run

# ── KEYWORD → DM RESPONSE MAP ────────────────────────────────────────────────
# When a comment contains a keyword, this DM is sent privately to the commenter.
# First match wins — put more specific keywords ABOVE general ones.
KEYWORD_RESPONSES = {
    ("align", "alignment", "free guide", "send it", "send me"): (
        "Hey! 💜 Here's your free ALIGN Guide — exactly what you asked for!\n\n"
        "https://mailchi.mp/10f79b32a6a0/align\n\n"
        "This is Amy's step-by-step method for finally getting your habits, "
        "identity, and self-talk aligned. Enjoy! 🌟\n\n"
        "— Fit For Excellence Team"
    ),
    ("fiber", "glp", "glp-1", "peptide", "ozempic", "wegovy", "nutrition plan"): (
        "Hey! 💜 Here's Amy's free Fiber Guide!\n\n"
        "https://mailchi.mp/3f4abcecea44/fiber\n\n"
        "This shows you how to get GLP-1 style results naturally through food — "
        "no injections needed. 🌿\n\n"
        "Let us know if you have questions!\n— Fit For Excellence Team"
    ),
    ("atomic", "summer", "summer challenge", "july", "summer program"): (
        "Hey!! 🌟 So glad you're interested in the Atomic Summer Challenge!\n\n"
        "Here are the details:\n"
        "📅 July 6 – August 30 (8 weeks)\n"
        "✅ $97 for 2 months — Amy has NEVER offered this price!\n"
        "✅ Customized plan built around YOUR life\n"
        "✅ Weekly coaching + accountability\n"
        "✅ Lose weight without missing summer fun\n\n"
        "Grab your spot here 👉 https://www.amylight.info/fitplustraining\n\n"
        "We're looking for 50 women — don't miss it! 💜\n"
        "— Coach Amy & Team"
    ),
    ("self talk", "selftalk", "thoughts", "mindset", "self-talk"): (
        "Hey! 💜 So glad this resonated with you!\n\n"
        "Here's Amy's free Self-Talk guide — it's where the real transformation starts:\n"
        "👉 https://amylight.netlify.app/page3-selftalk.html\n\n"
        "And if you want to take the 7-Day Thought Challenge:\n"
        "👉 https://amylight.netlify.app/page4-challenge.html\n\n"
        "This is the piece most programs completely miss. 🧠✨\n"
        "— Fit For Excellence Team"
    ),
    ("price", "cost", "how much", "$$", "pricing", "membership fee"): (
        "Hey! 💜 Great question!\n\n"
        "Fit Plus is $150/month — no contracts, cancel anytime, and there's a "
        "30-day money-back guarantee so there's zero risk.\n\n"
        "You get:\n"
        "💪 Daily guided workouts\n"
        "🥗 Nutrition guidance\n"
        "🧠 Self-talk coaching\n"
        "📲 Daily accountability from Amy\n"
        "👯 Community support\n\n"
        "Learn more and grab your spot 👉 https://www.amylight.info/fitplustraining\n\n"
        "— Fit For Excellence Team"
    ),
    ("quiz", "which program", "where do i start", "where to start", "best for me"): (
        "Hey! 💜 The best place to start is Amy's free 60-second quiz — "
        "it matches you to exactly the right program for YOUR life and goals!\n\n"
        "👉 https://amylight.netlify.app/quiz.html\n\n"
        "Takes less than a minute and Amy will personally follow up! 🌟\n"
        "— Fit For Excellence Team"
    ),
    ("interested", "info", "tell me more", "more info", "details", "sign me up", "join", "yes", "in!", "i'm in", "im in"): (
        "Hey!! So excited you're interested! 💜\n\n"
        "The best first step is taking Amy's free 60-second quiz — "
        "it'll match you to the perfect program:\n\n"
        "👉 https://amylight.netlify.app/quiz.html\n\n"
        "Amy personally follows up with everyone who takes it! 🌟\n"
        "— Fit For Excellence Team"
    ),
    ("love this", "this is me", "needed this", "so true", "omg", "wow", "🙌", "💜", "❤️", "fire", "🔥"): (
        "Hey! This made our day!! 💜🙌\n\n"
        "If this content is speaking to you, Amy has a free guide that goes even deeper:\n"
        "👉 https://amylight.netlify.app/quiz.html\n\n"
        "Takes 60 seconds and Amy will personally reach out. "
        "You're exactly who this community is for! 🌟\n"
        "— Coach Amy & Team"
    ),
}

# Default DM for ANY comment that doesn't match a keyword
# Set to None to only DM keyword matches and ignore everything else
DEFAULT_RESPONSE = (
    "Hey! Thanks so much for engaging with Amy's content — it truly means the world! 💜\n\n"
    "If you ever want to dive deeper into the ALIGN Method or find your perfect program, "
    "Amy's free 60-second quiz is the best place to start:\n\n"
    "👉 https://amylight.netlify.app/quiz.html\n\n"
    "Have an amazing day! 🌟\n— Fit For Excellence Team"
)

# ── API HELPERS ──────────────────────────────────────────────────────────────
def api_get(path, params=None):
    p = {"access_token": PAGE_TOKEN}
    if params:
        p.update(params)
    url = f"{BASE}/{path}?{urllib.parse.urlencode(p)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def api_post(path, data):
    data["access_token"] = PAGE_TOKEN
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

# ── STATE TRACKING ───────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"fb_comments": {}, "ig_comments": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── KEYWORD DETECTION ────────────────────────────────────────────────────────
def detect_keyword(text):
    """Returns (reply_text, matched_keyword) or (DEFAULT_RESPONSE, None)."""
    lower = text.lower().strip()
    for keywords, reply in KEYWORD_RESPONSES.items():
        for kw in keywords:
            if kw in lower:
                return reply, kw
    return DEFAULT_RESPONSE, None

# ── FACEBOOK ─────────────────────────────────────────────────────────────────
def get_fb_posts():
    result = api_get(f"{PAGE_ID}/feed", {
        "fields": "id,message,created_time",
        "limit": str(POSTS_TO_CHECK)
    })
    return result.get("data", [])

def get_fb_comments(post_id):
    result = api_get(f"{post_id}/comments", {
        "fields": "id,message,from,created_time",
        "limit": "50"
    })
    return result.get("data", [])

def send_fb_private_reply(comment_id, message):
    """Send a private DM reply to a Facebook commenter via private_replies endpoint."""
    return api_post(f"{comment_id}/private_replies", {"message": message})

def check_fb_comments(state):
    posts        = get_fb_posts()
    auto_replied = []
    needs_manual = []

    for post in posts:
        post_id      = post["id"]
        post_preview = (post.get("message") or "")[:50]
        comments     = get_fb_comments(post_id)

        for comment in comments:
            comment_id   = comment["id"]
            comment_text = comment.get("message", "")
            commenter    = comment.get("from", {})
            commenter_id = commenter.get("id", "")
            commenter_name = commenter.get("name", "Unknown")

            # Skip if already handled
            if state["fb_comments"].get(comment_id):
                continue

            # Skip if commenter is the page itself
            if commenter_id == PAGE_ID:
                state["fb_comments"][comment_id] = "skip_self"
                continue

            reply_text, matched_kw = detect_keyword(comment_text)

            if reply_text:
                result = send_fb_private_reply(comment_id, reply_text)
                if "id" in result or "success" in result:
                    state["fb_comments"][comment_id] = matched_kw or "default"
                    auto_replied.append({
                        "platform": "FB",
                        "name": commenter_name,
                        "comment": comment_text[:60],
                        "keyword": matched_kw or "(default)",
                        "post": post_preview
                    })
                else:
                    err = result.get("error", {}).get("message", str(result))
                    # Mark as attempted so we don't retry forever
                    state["fb_comments"][comment_id] = f"failed: {err[:50]}"
                    needs_manual.append({
                        "platform": "FB",
                        "name": commenter_name,
                        "comment": comment_text[:60],
                        "note": f"Private reply failed: {err[:80]}"
                    })
            else:
                state["fb_comments"][comment_id] = "no_match"

    return auto_replied, needs_manual

# ── INSTAGRAM ────────────────────────────────────────────────────────────────
def get_ig_media():
    result = api_get(f"{IG_ID}/media", {
        "fields": "id,caption,timestamp",
        "limit": str(POSTS_TO_CHECK)
    })
    return result.get("data", [])

def get_ig_comments(media_id):
    result = api_get(f"{media_id}/comments", {
        "fields": "id,text,from,timestamp",
        "limit": "50"
    })
    return result.get("data", [])

def send_ig_dm(commenter_igsid, message):
    """Send a private DM to an Instagram user by their IGSID."""
    data = {
        "recipient": json.dumps({"id": commenter_igsid}),
        "message": json.dumps({"text": message}),
        "access_token": PAGE_TOKEN
    }
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}/{PAGE_ID}/messages", data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def check_ig_comments(state):
    media_list   = get_ig_media()
    auto_replied = []
    needs_manual = []

    for media in media_list:
        media_id      = media["id"]
        media_preview = (media.get("caption") or "")[:50]
        comments      = get_ig_comments(media_id)

        for comment in comments:
            comment_id     = comment["id"]
            comment_text   = comment.get("text", "")
            commenter      = comment.get("from", {})
            commenter_id   = commenter.get("id", "")
            commenter_name = commenter.get("username", commenter.get("name", "Unknown"))

            # Skip if already handled
            if state["ig_comments"].get(comment_id):
                continue

            # Skip if commenter is Amy's own account
            if commenter_id == IG_ID:
                state["ig_comments"][comment_id] = "skip_self"
                continue

            reply_text, matched_kw = detect_keyword(comment_text)

            if reply_text and commenter_id:
                result = send_ig_dm(commenter_id, reply_text)
                if "message_id" in result or "id" in result:
                    state["ig_comments"][comment_id] = matched_kw or "default"
                    auto_replied.append({
                        "platform": "IG",
                        "name": commenter_name,
                        "comment": comment_text[:60],
                        "keyword": matched_kw or "(default)",
                        "post": media_preview
                    })
                else:
                    err = result.get("error", {}).get("message", str(result))
                    state["ig_comments"][comment_id] = f"failed: {err[:50]}"
                    needs_manual.append({
                        "platform": "IG",
                        "name": commenter_name,
                        "comment": comment_text[:60],
                        "note": f"IG DM failed: {err[:80]}"
                    })
            else:
                state["ig_comments"][comment_id] = "no_match_or_no_id"

    return auto_replied, needs_manual

# ── MAIN LOOP ────────────────────────────────────────────────────────────────
def run_check():
    print(f"\n{'='*60}")
    print(f"Comment Watcher — FB + IG Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    state = load_state()

    # Facebook
    print("Checking Facebook comments...")
    fb_replied, fb_manual = check_fb_comments(state)

    # Instagram
    print("Checking Instagram comments...")
    ig_replied, ig_manual = check_ig_comments(state)

    save_state(state)

    all_replied = fb_replied + ig_replied
    all_manual  = fb_manual  + ig_manual

    if all_replied:
        print(f"\n✅ AUTO-DM'D ({len(all_replied)}):")
        for r in all_replied:
            print(f"   [{r['platform']}] {r['name']} commented: \"{r['comment']}\"")
            print(f"   └─ keyword: '{r['keyword']}' | on post: \"{r['post']}\"")

    if all_manual:
        print(f"\n⚠️  FAILED / NEEDS ATTENTION ({len(all_manual)}):")
        for r in all_manual:
            print(f"   [{r['platform']}] {r['name']}: \"{r['comment']}\"")
            print(f"   └─ {r['note']}")

    if not all_replied and not all_manual:
        print("✓ No new comments to handle.")

    print(f"\nNext check in 30 minutes...")

if __name__ == "__main__":
    if "--once" in sys.argv:
        # GitHub Actions mode — run once and exit
        run_check()
    else:
        print("Comment Watcher running. Checks FB + IG every 30 min.")
        print("Press Ctrl+C to stop.\n")
        while True:
            try:
                run_check()
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M')}] Error: {e}")
            time.sleep(1800)  # 30 minutes

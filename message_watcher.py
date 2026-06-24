"""
message_watcher.py
------------------
Runs inside GitHub Actions every 15 minutes.
Checks Facebook + Instagram DMs, keyword-detects, and auto-replies.
State is tracked in fb_message_state.json + ig_message_state.json
which get committed back to the repo after each run.

GitHub Secrets required:
  PAGE_TOKEN  — Amy's long-lived Facebook Page token
  IG_ID       — Instagram Business Account ID
"""
import os, json, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
PAGE_TOKEN = os.environ.get("PAGE_TOKEN") or (
    open("page_token.txt").read().strip() if os.path.exists("page_token.txt") else None
)
PAGE_ID = "224952947543823"
IG_ID   = os.environ.get("IG_ID", "17841455628778748")
BASE    = "https://graph.facebook.com/v25.0"

FB_STATE_FILE = "fb_message_state.json"
IG_STATE_FILE = "ig_message_state.json"

if not PAGE_TOKEN:
    print("ERROR: PAGE_TOKEN not set.")
    sys.exit(1)

# ── KEYWORD → RESPONSE MAP ────────────────────────────────────────────────────
KEYWORD_RESPONSES = [
    (
        ["align", "ebook", "free guide", "free book"],
        "Hey! 💜 Here's Amy's free ALIGN Guide — your first step to getting "
        "your habits aligned with who you want to be!\n\n"
        "https://mailchi.mp/10f79b32a6a0/align\n\n"
        "Let me know if you have any questions! 🌟"
    ),
    (
        ["fiber", "glp", "peptide", "injection", "ozempic", "wegovy"],
        "Hey! 💜 Here's Amy's free Fiber Guide — it shows you how to get "
        "GLP-1 style results naturally through food!\n\n"
        "https://mailchi.mp/3f4abcecea44/fiber\n\n"
        "Let us know if you have questions! 🌿"
    ),
    (
        ["atomic", "summer challenge", "summer program", "july 6"],
        "Hey! 🌟 The Atomic Summer Challenge is Amy's 8-week program "
        "running July 6 – August 30!\n\n"
        "Designed for women who want to lose weight this summer WITHOUT "
        "putting their life on hold.\n\n"
        "✅ $97 for 2 months (Amy has NEVER offered this price!)\n"
        "✅ Customized plan built around YOUR life\n"
        "✅ Weekly coaching + accountability\n\n"
        "Grab your spot 👉 https://www.amylight.info/fitplustraining\n\n"
        "We're looking for 50 women — don't miss it! 💜"
    ),
    (
        ["price", "cost", "how much", "$$", "money", "rate", "fee", "charge", "pricing"],
        "Hey! Fit Plus is $150/month — no contracts and a 30-day money-back "
        "guarantee, so there's zero risk. 💜\n\n"
        "Daily workouts, nutrition guidance, self-talk coaching, "
        "and direct access to Amy every single day.\n\n"
        "Learn more 👉 https://www.amylight.info/fitplustraining"
    ),
    (
        ["quiz", "what program", "which program", "where do i start", "where to start", "best program"],
        "Hey! The best place to start is Amy's free 60-second quiz — "
        "it matches you to the perfect program for YOUR life!\n\n"
        "👉 https://amylight.netlify.app/quiz.html\n\n"
        "Takes less than a minute and Amy will personally follow up! 💜"
    ),
    (
        ["schedule", "book a call", "coaching call", "talk to amy", "discovery call"],
        "Love it! You can book a free discovery call with Amy right here 👇\n\n"
        "📅 https://cal.com/coachamylight/fitelite\n\n"
        "She'd love to connect and find the best fit for your goals! 💜"
    ),
    (
        ["join", "sign up", "sign me up", "i'm in", "im in", "how do i join", "how to join", "enroll"],
        "Amazing!! So excited to have you! 🎉💜\n\n"
        "Here's where you can grab your spot in Fit Plus:\n"
        "👉 https://www.amylight.info/fitplustraining\n\n"
        "Once you're in, Amy will personally reach out to get you set up! 🙌"
    ),
    (
        ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hola"],
        "Hey!! Welcome to Fit for Excellence! 💜 So glad you reached out!\n\n"
        "Amy will get back to you personally very soon. In the meantime, "
        "take our free 60-second quiz to find your perfect program:\n\n"
        "👉 https://amylight.netlify.app/quiz.html\n\n"
        "Have an amazing day! 🌟"
    ),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
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

def load_state(filepath):
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return {}

def save_state(filepath, state):
    with open(filepath, "w") as f:
        json.dump(state, f, indent=2)

def detect_keyword(text):
    lower = text.lower().strip()
    for keywords, reply in KEYWORD_RESPONSES:
        for kw in keywords:
            if kw in lower:
                return reply, kw
    return None, None

# ── FACEBOOK MESSAGES ─────────────────────────────────────────────────────────
def run_fb():
    print("\n── FACEBOOK MESSAGES ────────────────────────────────")
    state  = load_state(FB_STATE_FILE)
    result = api_get(f"{PAGE_ID}/conversations", {
        "fields": "participants,updated_time,unread_count",
        "limit": "25"
    })
    convos = result.get("data", [])

    if "error" in result:
        print(f"  FB API error: {result['error'].get('message', '')}")
        return state

    replied = 0
    skipped = 0

    for convo in convos:
        convo_id     = convo["id"]
        participants = convo.get("participants", {}).get("data", [])
        other        = next((p for p in participants if p["id"] != PAGE_ID), None)
        sender_name  = other["name"] if other else "Unknown"

        msgs   = api_get(f"{convo_id}/messages", {"fields": "message,from,created_time", "limit": "3"})
        latest = (msgs.get("data") or [None])[0]
        if not latest:
            continue

        msg_id   = latest.get("id", "")
        msg_text = latest.get("message", "")
        from_id  = latest.get("from", {}).get("id", "")

        # Skip if last message is from us or already handled
        if from_id == PAGE_ID or state.get(convo_id) == msg_id:
            skipped += 1
            continue

        reply_text, kw = detect_keyword(msg_text)
        if not reply_text:
            print(f"  ⚠ {sender_name}: no keyword match — needs manual reply")
            print(f"    Message: \"{msg_text[:70]}\"")
            skipped += 1
            continue

        res = api_post(f"{convo_id}/messages", {"message": reply_text})
        if "id" in res:
            state[convo_id] = msg_id
            replied += 1
            print(f"  ✓ {sender_name}: auto-replied (keyword: '{kw}')")
        else:
            err = res.get("error", {}).get("message", str(res))
            print(f"  ✗ {sender_name}: reply failed — {err[:80]}")

    print(f"  FB: {replied} replied, {skipped} skipped")
    save_state(FB_STATE_FILE, state)
    return state

# ── INSTAGRAM MESSAGES ────────────────────────────────────────────────────────
def run_ig():
    print("\n── INSTAGRAM MESSAGES ───────────────────────────────")
    state  = load_state(IG_STATE_FILE)
    result = api_get(f"{PAGE_ID}/conversations", {
        "platform": "instagram",
        "fields": "participants,updated_time,messages{message,from,created_time,id}",
        "limit": "25"
    })
    convos = result.get("data", [])

    if "error" in result:
        # Fallback: try via IG user ID
        result = api_get(f"{IG_ID}/conversations", {
            "fields": "participants,updated_time,messages{message,from,created_time,id}",
            "limit": "25"
        })
        convos = result.get("data", [])

    if "error" in result:
        print(f"  IG API error: {result.get('error', {}).get('message', '')}")
        return state

    replied = 0
    skipped = 0

    for convo in convos:
        convo_id     = convo["id"]
        participants = convo.get("participants", {}).get("data", [])
        other        = next((p for p in participants if p.get("id") != IG_ID), None)
        sender_name  = other.get("name", "Unknown") if other else "Unknown"
        sender_ig_id = other.get("id") if other else None

        messages = convo.get("messages", {}).get("data", [])
        if not messages:
            continue

        latest   = messages[0]
        msg_id   = latest.get("id", "")
        msg_text = latest.get("message", "")
        from_id  = latest.get("from", {}).get("id", "")

        if from_id in [IG_ID, PAGE_ID] or state.get(convo_id) == msg_id:
            skipped += 1
            continue

        reply_text, kw = detect_keyword(msg_text)
        if not reply_text:
            print(f"  ⚠ {sender_name}: no keyword match — needs manual reply")
            print(f"    Message: \"{msg_text[:70]}\"")
            skipped += 1
            continue

        # Try via conversation endpoint, fallback to Send API
        res = api_post(f"{convo_id}/messages", {"message": reply_text})
        if "error" in res:
            res = api_post(f"{PAGE_ID}/messages", {
                "recipient": json.dumps({"id": sender_ig_id}),
                "message": json.dumps({"text": reply_text})
            })

        if "id" in res or "message_id" in res:
            state[convo_id] = msg_id
            replied += 1
            print(f"  ✓ {sender_name}: auto-replied (keyword: '{kw}')")
        else:
            err = res.get("error", {}).get("message", str(res))
            print(f"  ✗ {sender_name}: reply failed — {err[:80]}")

    print(f"  IG: {replied} replied, {skipped} skipped")
    save_state(IG_STATE_FILE, state)
    return state

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Message Watcher — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    run_fb()
    run_ig()
    print("\nDone.")

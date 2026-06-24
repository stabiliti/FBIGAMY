"""
atomic_summer_posts.py
-----------------------
Facebook/Instagram caption bank for the Atomic Summer Challenge.

67 posts matching the email campaign (June 25 – Aug 30):
  • 11 pre-launch posts (June 25 – July 5)
  • 56 daily challenge posts (July 6 – Aug 30)

Options:
  py atomic_summer_posts.py              → Browse / preview all captions
  py atomic_summer_posts.py --post N     → Post caption #N to Facebook NOW
  py atomic_summer_posts.py --schedule   → Schedule all 67 posts on Facebook
                                           (same time slots as email campaign)
  py atomic_summer_posts.py --ig N       → Print caption #N formatted for IG copy-paste

NOTE: Instagram does not support scheduled publishing via API without a
      Creator Studio workflow. IG captions are printed for manual copy-paste.
      Facebook posts ARE scheduled automatically via the Graph API.
"""
import urllib.request, urllib.error, json, urllib.parse, os, sys, time
from datetime import datetime, timedelta, timezone

# ── CONFIG ───────────────────────────────────────────────────────────────────
PAGE_TOKEN  = open("page_token.txt").read().strip() if os.path.exists("page_token.txt") else "PASTE_PAGE_TOKEN_HERE"
PAGE_ID     = "224952947543823"
IG_ID       = "17841455628778748"   # Instagram Business Account ID (linked to this FB Page)
BASE        = "https://graph.facebook.com/v25.0"
SIGNUP_URL  = "https://www.amylight.info/fitplustraining"
IMAGES_DIR  = "atomic_summer_images"   # Run download_assets.py once to populate this

# ── IMAGE ASSIGNMENT MAP ─────────────────────────────────────────────────────
# One image per post (index 0 = post #1).
# Run  py download_assets.py  first so these files exist locally.
# HEIC files are iPhone-only; FB accepts JPG/PNG/WEBP — skip or convert heic.
#
# Key for filenames (after running download_assets.py):
#   img_2814_habits_compound.jpg       → "Small habits don't add up, they COMPOUND" graphic
#   img_3063_atomic_summer_ad.jpg      → Atomic Summer landing/ad screenshot
#   img_5168_workbook_cover.jpg        → Atomic Summer workbook cover
#   img_5169_goals_worksheet.jpg       → Challenge goals worksheet
#   img_5170_understanding_goals.jpg   → Understanding goals worksheet
#   img_0161_atomic_habits_book.jpg    → Atomic Habits book (James Clear)
#   img_0803_book_morning.jpg          → Atomic Habits book in morning setting
#   img_3435_i_am_consistent.jpg       → "I AM CONSISTENT AND I SHOW UP FOR MYSELF"
#   img_0306_client_testimonial.jpg    → Client: "I found my home" testimonial
#   img_5f5a_client_menopause.jpg      → Client menopause transformation testimonial
#   img_6239_cant_wait_atomic.jpg      → Client: "I can't wait for Atomic Summer!"
#   img_6652_seana_accountability.png  → Seana accountability text screenshot
#   img_5203_morning_routine.jpg       → Client morning routine habit stacking
#   img_3055_screenshot.jpg            → Screenshot (open and rename as needed)
#   img_a18d_unknown.jpg               → Open and rename after downloading
#   img_511a_unknown.jpg               → Open and rename after downloading
#
IMAGE_MAP = [
    # ── PRE-LAUNCH (posts 1–11) ───────────────────────────────────────────────
    "511AB7E1-63AA-4972-90B8-B03DF5B8B245.JPG",  # 1  — Something big is coming (Atomic Summer Guidebook tease)
    "35.jpg",                # 2  — Honest about the cycle (What story are you telling yourself)
    "Habit 1.jpg",           # 3  — Introducing Atomic Summer (Habit #1: Align Your Thoughts)
    "41.jpg",                # 4  — What's an atomic habit (Neuroplasticity science graphic)
    "5F5A6142-1064-4A85-87A5-2D0F0F8444F4.JPG",          # 5  — What 6 weeks can do (real client transformation at pool)
    "50.jpg",                # 6  — Looking for 50 women (Amy red bikini — transformation visual)
    "A18D0E6C-7169-4EB9-916D-B1414F39EC2D.JPG",          # 7  — Why $97 (real client DM — 12-week journey proof)
    "34.jpg",                # 8  — Message from Amy (Amy with surfboard — personal photo)
    "18.jpg",                # 9  — FAQ (Q&A Ask Anything graphic)
    "21.jpg",                # 10 — Happy 4th of July (Amy + friends at beach — summer fun)
    "Habit 2.jpg",           # 11 — TOMORROW last chance (Habit #2: Lifestyle Before Willpower)
    # ── CHALLENGE WEEK 1: Days 1–7 (July 6–12) ───────────────────────────────
    "1.jpg",                 # 12 — Day 1 (Amy quote — born with unlimited potential)
    "33.jpg",                # 13 — Day 2: Never Miss Twice (confidence starts with believing in YOU)
    "43.jpg",                # 14 — Day 3: Not lazy (Your BS = your belief system)
    "4.jpg",                 # 15 — Day 4: Self-talk shifts (Tip 2: Practice Positive Self-Talk)
    "9.jpg",                 # 16 — Day 5: Nutrition (Prioritize self-care — mind body soul)
    "45.jpg",                # 17 — Day 6: Check in (two women playing in ocean — community)
    "56.jpg",                # 18 — Day 7: Week 1 complete (family beach hug — celebrate every win)
    # ── CHALLENGE WEEK 2: Days 8–14 (July 13–19) ─────────────────────────────
    "36.jpg",                # 19 — Day 8: Who are you becoming (you have the power to rewrite your story)
    "57.jpg",                # 20 — Day 9: Visualization (life collage + confidence quote)
    "60.jpg",                # 21 — Day 10: Guilt (when you change how you talk to yourself...)
    "23.jpg",                # 22 — Day 11: 2-Minute Rule (Amy at NPC fitness competition — action)
    "58.jpg",                # 23 — Day 12: Self-talk check-in (What story are you telling yourself)
    "27.jpg",                # 24 — Day 13: Food freedom (life collage — beach, surfing, wedding)
    "22.jpg",                # 25 — Day 14: Two weeks (multiple client testimonial screenshots)
    # ── CHALLENGE WEEK 3: Days 15–21 (July 20–26) ────────────────────────────
    "44.jpg",                # 26 — Day 15: Protein (Amy at desk — what thoughts hold you back)
    "59.jpg",                # 27 — Day 16: Fiber (notes card on sunset beach — simple truth)
    "46.jpg",                # 28 — Day 17: Hydration (Amy surfboard straw hat — summer vibe)
    "38.jpg",                # 29 — Day 18: Sleep (This one thing could change EVERYTHING)
    "31.jpg",                # 30 — Day 19: Mid-summer drift (What's Holding You Back?)
    "8.jpg",                 # 31 — Day 20: Emotional eating (3 Tips to improve self-worth)
    "32.jpg",                # 32 — Day 21: 21-day milestone (transformed by renewing your mind)
    # ── CHALLENGE WEEK 4: Days 22–28 (July 27 – Aug 2) ──────────────────────
    "11.jpg",                # 33 — Day 22: Consistency (tweet-style — What if you finally believed)
    "Habit 2.jpg",           # 34 — Day 23: Habit stacking (Habit #2: Lifestyle Before Willpower)
    "39.jpg",                # 35 — Day 24: Environment design (Ready to achieve your goals)
    "28.jpg",                # 36 — Day 25: Accountability (life collage + Mackenzie Totten testimonial)
    "29.jpg",                # 37 — Day 26: Comeback (life collage + Laurén Lambert testimonial)
    "5F5A6142-1064-4A85-87A5-2D0F0F8444F4.JPG",          # 38 — Day 27: Non-scale victories (client strong at pool)
    "30.jpg",                # 39 — Day 28: Four weeks halfway (Kristi Hohm Sommer testimonial)
    # ── CHALLENGE WEEK 5: Days 29–35 (Aug 3–9) ───────────────────────────────
    "45.jpg",                # 40 — Day 29: Vacation plan (two women in ocean — summer freedom)
    "42.jpg",                # 41 — Day 30: 30 days (Amy — you don't have to stay stuck)
    "55.jpg",                # 42 — Day 31: Motivation (Amy gold sequin Jeep — practice self-talk)
    "19.jpg",                # 43 — Day 32: Comparison trap (Unlock Your Unlimited Potential)
    "48.jpg",                # 44 — Day 33: Strength training (Amy surfboard + Neurofit mindset)
    "26.jpg",                # 45 — Day 34: Tag a friend (Join Amy LIVE — community life collage)
    "54.jpg",                # 46 — Day 35: Five weeks (Amy white dress — Challenge Your Thoughts)
    # ── CHALLENGE WEEK 6: Days 36–42 (Aug 10–16) ─────────────────────────────
    "41.jpg",                # 47 — Day 36: Habit becoming automatic (neuroplasticity — brain rewiring)
    "44.jpg",                # 48 — Day 37: Do it first (Amy at desk — morning energy)
    "5F5A6142-1064-4A85-87A5-2D0F0F8444F4.JPG",          # 49 — Day 38: Menopause + metabolism (older woman strong at pool — perfect match)
    "34.jpg",                # 50 — Day 39: Progress photo (Amy surfboard — transformation visual)
    "24.jpg",                # 51 — Day 40: 40 days in (client self-talk affirmations screenshots)
    "47.jpg",                # 52 — Day 41: After Aug 30 (Amy + husband beach wedding — new beginning)
    "50.jpg",                # 53 — Day 42: Six weeks (Amy at cenote — extraordinary)
    # ── CHALLENGE WEEK 7: Days 43–49 (Aug 17–23) ─────────────────────────────
    "52.jpg",                # 54 — Day 43: Final stretch (Amy + husband sunset wedding dance)
    "3.jpg",                 # 55 — Day 44: Self-talk at finish line (Tip 1: Challenge Your Thoughts)
    "53.jpg",                # 56 — Day 45: 45 days of evidence (Amy sunset + self-doubt search bar)
    "51.jpg",                # 57 — Day 46: They're watching (family beach hug + real client results)
    "36.jpg",                # 58 — Day 47: Final push (You have power to rewrite your story)
    "58.jpg",                # 59 — Day 48: Letter to self (notes — What story are you telling yourself)
    "49.jpg",                # 60 — Day 49: Seven weeks (Amy + husband wedding + 8-module coaching)
    # ── CHALLENGE WEEK 8: Days 50–56 (Aug 24–30) ─────────────────────────────
    "1.jpg",                 # 61 — Day 50: Final 7 days (Amy unlimited potential — full circle)
    "37.jpg",                # 62 — Day 51: Identity permanent (you have power to rewrite story — teal)
    "60.jpg",                # 63 — Day 52: Your takeaway (change how you talk = change your reality)
    "30.jpg",                # 64 — Day 53: Three days left (Kristi testimonial — keep going)
    "46.jpg",                # 65 — Day 54: Two days (Amy surfboard — run through the tape)
    "48.jpg",                # 66 — Day 55: Last night (Amy surfboard + mindset transformation)
    "A18D0E6C-7169-4EB9-916D-B1414F39EC2D.JPG",          # 67 — Day 56: YOU DID IT 🎉 (real DM — daughter inspired, full circle)
]

# ── SEND TIME SLOTS (UTC) — matches email campaign ───────────────────────────
# Slots rotate so FB can track which time gets best engagement
SLOTS = [
    (18, 30, 0),   # Slot A: 11:30 AM PDT
    (19, 30, 0),   # Slot B: 12:30 PM PDT
    (21,  0, 0),   # Slot C:  2:00 PM PDT
    ( 1,  0, 1),   # Slot D:  6:00 PM PDT (01:00 UTC next day)
]
SLOT_LABELS = ["11:30 AM", "12:30 PM", "2:00 PM", "6:00 PM"]

def send_time_unix(base_date, slot_index):
    """Return Unix timestamp for publishing (required by FB scheduled_publish_time)."""
    h, m, extra = SLOTS[slot_index % 4]
    dt = base_date.replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=timezone.utc)
    dt += timedelta(days=extra)
    return int(dt.timestamp())

# ── CAPTION BANK ─────────────────────────────────────────────────────────────
# Each caption is a string. Hashtags included at the bottom of each post.
# Signup link is woven in where natural; always present for pre-launch posts.

CAPTIONS = [
# ── PRE-LAUNCH 1–11 (June 25 – July 5) ──────────────────────────────────────
"""Something BIG is coming July 6. 🌟

I've been quietly building something I've never done before — and I'm almost ready to share it.

If you've ever had a summer that felt like it slipped away... this is for you.

Stay close. Details drop this week. Save this post. 💜

#FitForExcellence #AtomicSummer #ComingSoon #WomensWellness #FitnessCoach #WomensFitness #SummerFitness #FitnessMotivation #HealthCoach #WomenOver40 #FitOver40 #MidlifeWellness #WeightLossJourney #SummerBody #HealthyLifestyle #FitnessChallenge #6WeekChallenge #CoachAmy #AmyLight #FitnessGoals""",

"""Can I be honest with you for a second? 💜

Every summer I watch women I love go through the same cycle.

✨ Starts June feeling motivated.
😔 July 4th throws them off.
😤 "I'll restart in August."
🍂 "I'll do it in September."

And then summer is just... over. Again.

This is NOT a willpower problem. It's a STRATEGY problem.

I'm doing something about it. July 6. Watch this space. 👀

Save this post — you'll want the details when they drop.

#FitForExcellence #AtomicSummer #SummerFitness #FitnessMotivation #WomenWhoLift #WomensWellness #WeightLoss #HealthyHabits #MindsetShift #SelfTalk #FitOver40 #WomenOver40 #MidlifeHealth #FitnessJourney #HealthCoach #CoachAmy #WomenSupportingWomen #FitnessInspiration #SummerGoals #BodyTransformation""",

"""INTRODUCING: The Atomic Summer Challenge ☀️🔥

6 weeks. July 6 – August 30.

Built specifically for women who want to lose weight this summer WITHOUT putting their life on hold.

✅ No crash diets
✅ No skipping vacations
✅ No giving up BBQs and family fun
✅ No "starting over Monday"

Just ONE atomic habit — chosen for YOUR life — that builds into something powerful by August 30.

$97 for 2 full months. I have NEVER offered this price.

Link in bio to grab your spot 👉 or DM me "SUMMER" and I'll send you everything. 💜

#AtomicSummer #FitForExcellence #FitnessChallenge #SummerChallenge #CoachAmy #WeightLoss #WomensWellness #FitOver40 #WomenOver40 #6WeekChallenge #HabitChallenge #AtomicHabits #SummerFitness #FitnessGoals #HealthyLifestyle #WeightLossJourney #WomensHealth #FitnessCoach #MidlifeWellness #WomenSupportingWomen""",

"""What's an atomic habit? Let me explain. 🔑

"Atomic" means tiny. Foundational. Small enough to survive your hardest day.

Here's what I've learned coaching women for 10+ years:

👉 The habit isn't the hard part. The BELIEF is.

When you repeat a small action every day AND tell yourself "I'm the kind of woman who shows up for herself" — your brain starts to believe it.

Your identity shifts. Showing up feels NATURAL instead of forced.

That's what we're building in Atomic Summer. July 6 – August 30.

$97 for 6 weeks. Link in bio. 💜

#AtomicHabits #IdentityBasedHabits #FitForExcellence #AtomicSummer #SummerFitness #HabitFormation #MindsetCoach #SelfTalk #SelfTalkTrainer #FitnessCoach #WomensWellness #FitOver40 #WomenOver40 #NeuroplasticityTraining #IdentityShift #HabitChallenge #GrowthMindset #WomensFitness #CoachAmy #MindBodyConnection""",

"""What can 6 weeks actually do? Let me show you. 💪

Picture this: it's August 30. Atomic Summer is over.

You went on vacation. ✅
You went to cookouts. ✅
You had the birthday cake. ✅
You showed up for yourself every single day anyway. ✅

8–15 lbs lighter. Not from suffering — from building one small habit that compounded over 6 weeks.

More importantly? You look in the mirror and you actually LIKE what you see — not because your body is perfect, but because you KEPT YOUR PROMISE TO YOURSELF.

THAT is what 6 weeks looks like.

$97. July 6. 50 women. Link in bio to join us. 💜

#AtomicSummer #FitForExcellence #SummerTransformation #FitnessJourney #RealResults #BeforeAndAfter #WeightLossJourney #6WeekChallenge #FitnessChallenge #WomensWellness #FitOver40 #WomenOver40 #BodyTransformation #HealthyLifestyle #FitnessGoals #SummerBody #FatLoss #FitnessMotivation #WomensFitness #MidlifeWellness""",

"""I'm looking for 50 women. 🙋‍♀️

Not perfect women. Not women who have it all figured out.

Women who are TIRED of starting over every Monday — and ready to try something that actually works.

Women who are done letting summer slip away again.

Women who are ready to say: "This time it's different. This time I'm building it right."

Is that you?

If so — Atomic Summer starts July 6 and your spot is waiting.

$97 for 6 weeks. 30-day money-back guarantee. Zero risk.

Drop "SUMMER" in the comments and I'll DM you the details. 💜

#AtomicSummer #FitForExcellence #FitnessChallenge #WeightLoss #WomenWhoLift #SummerFitness #FitnessMotivation #WomensWellness #FitOver40 #WomenOver40 #HealthCoach #SummerChallenge #FitnessGoals #WomenSupportingWomen #BodyTransformation #HealthyLifestyle #CoachAmy #MidlifeWellness #FitnessJourney #FatLoss""",

"""Why $97? Let me explain. 💜

Fit Plus is normally $150/month.

Atomic Summer gives you 2 full months for $97 total. That's less than $12 a week.

Why?

Because my goal this summer is ONE thing: get 50 women real results that they can share with the world.

I want your testimonial on August 31. I want your before-and-after story. I want to prove — again — that this method works for EVERY woman at EVERY stage.

You get every workout. Every coaching session. The full Fit Plus experience. Summer price.

This offer disappears when spots fill OR when July 6 arrives — whichever comes first.

Link in bio. Or DM me "SUMMER." 💜

#FitForExcellence #AtomicSummer #FitnessOffer #SummerDeal #CoachAmy #WomensWellness #FitOver40 #WomenOver40 #AffordableFitness #FitnessCoach #HealthCoach #WeightLoss #SummerFitness #FitnessMotivation #WomensFitness #MidlifeWellness #FitnessChallenge #WomenWhoLift #HealthyLifestyle #6WeekChallenge""",

"""A message from me to you. 💌

I lost 50 pounds. I'm a national-level bodybuilder. I've coached women for 10+ years.

But what most people don't know is that I used to be completely controlled by food.

Stressed → ate. Lonely → ate. Exhausted → ate. Bored → ate.

I thought I was addicted. That I'd always be this way.

What changed wasn't a diet.

It was the conversation in my head.

I learned to talk to myself the way I'd talk to a woman I love. And everything shifted. The food noise stopped. The habit became natural. The weight came off — and stayed off.

THAT is what I want to give you this summer.

July 6. Atomic Summer. Link in bio. 💜

— Amy

#FitForExcellence #AtomicSummer #SelfTalk #CoachAmy #WomensWellness #SelfTalkTrainer #MindsetCoach #FoodNoise #WeightLoss #FitnessMotivation #WomensHealth #FitOver40 #WomenOver40 #BodyPositive #MindBodyConnection #SummerFitness #FitnessJourney #HealthCoach #WomenWhoLift #TransformationStory""",

"""Your questions about Atomic Summer — answered! ✅

Save this post — you'll want to come back to it. 🔖

❓ Do I need a gym?
👉 Nope. All workouts can be done at home. 10–45 min, your level.

❓ What if I go on vacation?
👉 That's literally the point. Atomic Summer TRAVELS WITH YOU.

❓ I've tried everything and nothing worked. Why is this different?
👉 Because we fix the root problem: the voice in your head. Willpower fails. Identity doesn't.

❓ What if I fall off track?
👉 Never miss twice is the only rule. Amy is in your corner the full 6 weeks.

❓ What does it cost?
👉 $97 for 2 full months. 30-day money-back guarantee.

❓ When does it start?
👉 July 6!

DM me "SUMMER" or link in bio to grab your spot. 💜

#AtomicSummer #FitForExcellence #FAQ #SummerFitness #CoachAmy #FitnessChallenge #WomensWellness #FitOver40 #WomenOver40 #HomeWorkout #FitnessMotivation #HealthCoach #WeightLoss #FitnessGoals #WomensFitness #MidlifeWellness #HabitChallenge #IdentityBasedHabits #WomenWhoLift #6WeekChallenge""",

"""Happy 4th of July! 🇺🇸✨

Today we celebrate freedom. I want to talk about a different kind.

Freedom from:
🚫 Earning your food before you enjoy it
🚫 Punishing yourself for yesterday
🚫 Starting over every Monday
🚫 Feeling guilty at every cookout

Atomic Summer starts in 2 DAYS and we're declaring independence from ALL of it.

Enjoy today fully. Have the hot dog. Watch the fireworks. Hug your people.

Then join us July 6 for 6 weeks that will actually change things. 💜

$97 · Link in bio · 2 days left

#HappyFourthOfJuly #FitForExcellence #AtomicSummer #FoodFreedom #Independence #4thOfJuly #SummerFitness #FitnessMotivation #WomensWellness #FitOver40 #WomenOver40 #FoodGuilt #NoMoreDiets #HealthyMindset #FitnessChallenge #WeightLoss #MidlifeWellness #CoachAmy #WomenSupportingWomen #SummerBody""",

"""TOMORROW. ⏰

Atomic Summer starts July 6 — and that's TOMORROW.

If you've been on the fence: this is your moment.

Not Monday. Not August 1. Not "when things calm down."

Tomorrow.

Here's what happens when you join today:
1️⃣ Instant access to Fit Plus
2️⃣ Amy personally welcomes you in
3️⃣ Tomorrow morning: your FIRST Atomic Summer workout

$97 · 2 months · 30-day guarantee · Link in bio

This time next year you'll either say "I wish I had" — or "I'm so glad I did."

Which story do you want? 💜

#AtomicSummer #FitForExcellence #LastChance #StartTomorrow #CoachAmy #SummerFitness #FitnessChallenge #WomensWellness #FitOver40 #WomenOver40 #WeightLoss #FitnessMotivation #JoinNow #FitnessJourney #HealthyLifestyle #MidlifeWellness #WomenWhoLift #FitnessGoals #NowOrNever #6WeekChallenge""",

# ── CHALLENGE: Days 1–7 (July 6–12) WEEK 1 ──────────────────────────────────
"""Day 1 of Atomic Summer is HERE. 🔥

To every woman who signed up — YOU SHOWED UP.

That matters more than you know. A lot of people intended to start today. You actually did.

Your only job today: Complete your workout. Then say out loud — hand on heart:

"I am someone who shows up for herself."

It might feel weird. Say it anyway.

The self-talk piece isn't fluffy. It's the FOUNDATION everything else is built on.

Let's go. Day 1. We're doing this. 💜

Drop a 🔥 if you're IN!

#AtomicSummer #Day1 #FitForExcellence #ShowedUp #FitnessChallenge #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #SelfTalk #IdentityBasedHabits #HabitChallenge #WeightLoss #HealthyLifestyle #FitnessJourney #WomensFitness #MindsetShift #CoachAmy #UnlimitedPotential""",

"""The ONE rule of Atomic Summer. 📋

NEVER MISS TWICE.

That's it. That's the whole framework.

Miss a day? Life happens. Totally fine.

But you NEVER let one miss become two. Because two becomes three. And three becomes "I'll start again Monday."

This rule is a permission slip AND a commitment at the same time.

Grace + accountability. Both.

Save this rule. You'll need it. 💜

Day 2 of Atomic Summer. Let's go.

#AtomicSummer #Day2 #NeverMissTwice #FitnessRules #FitForExcellence #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #HabitFormation #FitnessMotivation #ConsistencyOverPerfection #AtomicHabits #FitnessChallenge #HealthyLifestyle #MindsetCoach #WomensFitness #CoachAmy #FitnessJourney #SelfCompassion""",

"""You are NOT lazy. 🧠

I need you to hear that. Really hear it.

The women I work with are some of the most driven, capable, hard-working women I know. They run families, businesses, careers.

They are NOT lazy.

What they are is MISALIGNED.

When your habits don't match your identity, the friction feels impossible. When they do — it feels natural. Almost automatic.

The goal of Atomic Summer isn't to white-knuckle your way through 6 weeks.

It's to BUILD the alignment between who you ARE and how you SHOW UP.

Tag a woman who needs to hear this today. 💜

Day 3. Let's build it.

#AtomicSummer #Day3 #FitForExcellence #SelfTalk #IdentityBasedHabits #YouAreNotLazy #MindsetCoach #WomensWellness #FitOver40 #WomenOver40 #HabitFormation #FitnessMotivation #IdentityShift #SelfTalkMatters #FitnessChallenge #WomensFitness #GrowthMindset #CoachAmy #HealthyHabits #AlignedLiving""",

"""What you say to yourself matters MORE than what you eat. 💬

Here's a shift I want you to try today:

OLD: "I always quit."
NEW: "I am LEARNING to follow through."

OLD: "I have no willpower."
NEW: "I am building the skill of consistency."

OLD: "I'll probably mess this up too."
NEW: "I show up even when it's hard."

Say the new ones. Out loud. 10 times. Even if they feel fake.

Your brain doesn't know the difference between what's true right now and what you're training it to believe. Feed it the good stuff. 🧠

Save this — come back to it on your hard days. 💜

Day 4, Atomic Summer.

#AtomicSummer #Day4 #SelfTalk #FitForExcellence #MindsetShift #SelfTalkMatters #PositiveSelfTalk #InnerVoice #SelfTalkTrainer #WomensWellness #FitOver40 #WomenOver40 #MindsetCoach #NeuroplasticityTraining #FitnessMotivation #AffinityStatements #GrowthMindset #WomensFitness #HealthyMindset #CoachAmy""",

"""Nutrition this summer — the SIMPLE version. 🥗

No tracking. No macros. No calorie counting.

Just three questions at every meal:

1️⃣ Does this have protein?
2️⃣ Am I actually hungry or am I bored/stressed/tired?
3️⃣ Can I eat this slowly and actually enjoy it?

That's it. That's the whole framework.

This is how my clients eat through BBQs, vacations, and all of summer — and STILL lose weight.

Save this post and try it at your next meal. 💜

Day 5 of Atomic Summer.

#AtomicSummer #Day5 #NutritionTips #FitForExcellence #SummerEating #IntuitiveEating #FoodFreedom #HealthyEating #WeightLoss #NutritionCoach #FitOver40 #WomenOver40 #MindfulEating #ProteinGoals #SummerNutrition #HealthyLifestyle #FitnessMotivation #WomensWellness #CleanEating #CoachAmy""",

"""Almost through Week 1 — check in with me! 🎉

Quick questions for yourself today:

✅ What went WELL this week?
✅ What was harder than expected?
✅ What are you PROUD of?

Write these down. Seriously.

Your brain needs to see the evidence of your effort to keep building the belief that you're someone who follows through.

Drop your answer in the comments — I read every single one. How is Atomic Summer going for you? 💜

Day 6.

#AtomicSummer #Day6 #WeeklyCheckIn #FitForExcellence #Progress #FitnessJourney #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #Accountability #FitnessMotivation #WomensFitness #CommunityLove #SelfReflection #HabitChallenge #HealthyLifestyle #CoachAmy #NonScaleVictory #GrowthMindset""",

"""WEEK 1 COMPLETE. ✅

Seven days. You showed up.

Say this out loud right now: "I am a woman who keeps her commitments."

Because you just proved it. SEVEN days in a row.

Week 2 is where the magic starts to happen. The first week is about starting. Week 2 is about MOMENTUM.

That's when the energy shifts. Sleep improves. The voice in your head gets quieter. The habit starts to feel like... just what you do.

You're right on schedule. Tag someone who needs to see this. 💜

#AtomicSummer #Week1Done #FitForExcellence #Consistency #FitnessJourney #Week1 #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #HabitFormation #FitnessMotivation #IdentityBasedHabits #Momentum #WomensFitness #SevenDays #HealthyHabits #CoachAmy #SelfBelief #FinishersMindset""",

# ── CHALLENGE: Days 8–14 (July 13–19) WEEK 2 ────────────────────────────────
"""Who are you BECOMING? 🦋

Most people set goals. Lose 20 lbs. Work out 5 times a week.

The problem with goals: once you reach them, you have no reason to keep going.

Identity is different.

Instead of "What do I want?" — ask "Who do I want to BECOME?"

When you decide you're a woman who takes care of her body — the workouts aren't a task. They're EVIDENCE of who you are.

Today's practice: Write one sentence.
"I am a woman who __________."

Fill in who you're becoming. Keep it visible. 💜

Day 8 of Atomic Summer. Drop yours in the comments 👇

#AtomicSummer #Day8 #IdentityShift #FitForExcellence #BecomingHer #WomensWellness #FitOver40 #WomenOver40 #IdentityBasedHabits #MindsetCoach #SelfTalk #FitnessMotivation #WomensFitness #HabitFormation #GrowthMindset #FitnessChallenge #SummerFitness #CoachAmy #FutureSelf #AtomicHabits""",

"""Close your eyes for 2 minutes with me. 💜

Picture the version of you that exists on August 30.

The woman who finished Atomic Summer. She's not perfect — but she SHOWED UP.

What does she look like? How does she carry herself?
What does she say to herself in the morning?
How does she feel at the end of a long day?

See her clearly. Feel it. Then open your eyes and do ONE thing that woman would do today.

That's the practice. Do it every day and watch what happens.

Drop 💜 in the comments if this gave you chills.

Day 9 of Atomic Summer.

#AtomicSummer #Day9 #Visualization #FitForExcellence #FutureSelf #VisualizationTechnique #MindsetCoach #SelfTalk #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #BecomingHer #ManifestYourLife #FitnessJourney #WomensFitness #GrowthMindset #AttractionLaw #SummerFitness #CoachAmy""",

"""Guilt is NOT a strategy. 🔓

Here's the cycle that keeps women stuck:

😤 Feel bad → try harder → slip up → feel terrible → try harder → slip up → give up.

Guilt creates shame. Shame creates hiding. Hiding creates quitting.

Here's the replacement:

✅ Slip up → acknowledge without drama → ask "what can I learn?" → move forward.

The difference between women who GET results and women who don't isn't the slip-ups.

It's what they do AFTER.

Save this — you'll need it. 💜

Day 10. Break the cycle.

#AtomicSummer #Day10 #GuiltFree #FitForExcellence #FitnessMotivation #NoGuilt #FoodGuilt #WomensWellness #FitOver40 #WomenOver40 #SelfCompassion #MindsetCoach #BreakTheCycle #SelfTalk #FitnessChallenge #HealthyMindset #WomensFitness #GrowthMindset #CoachAmy #SummerFitness""",

"""The 2-Minute Rule — use it today. ⏱️

On days when you don't feel like it at ALL — the goal isn't the full workout.

The goal is to start for 2 minutes.

Put on your shoes. Open the app. Do the first exercise.

THEN watch what happens. 99% of the time the momentum carries you through.

Not because willpower kicked in. Because STARTING is the hardest part.

Day 11 of Atomic Summer. 2 minutes. That's all. 💜

#AtomicSummer #Day11 #2MinuteRule #FitForExcellence #StartSmall #AtomicHabits #HabitFormation #FitnessMotivation #WomensWellness #FitOver40 #WomenOver40 #JustStart #NoExcuses #FitnessChallenge #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #TinyHabits #MomentumBuilder""",

"""Real talk — how's your self-talk this week? 🎙️

Today I want you to notice what you say to yourself when you:

👀 Look in the mirror
⚖️ Step on the scale
🍕 Make a food choice you're not proud of
😴 Miss a workout

Don't fix it today. Just NOTICE.

Awareness is Step 1. You can't change what you can't see.

What's the loudest negative thing your inner voice says? Drop it in the comments — let's flip it together. 💜

Day 12 of Atomic Summer.

#AtomicSummer #Day12 #SelfTalk #FitForExcellence #MindsetWork #SelfTalkTrainer #InnerCritic #SelfTalkMatters #WomensWellness #FitOver40 #WomenOver40 #MindsetCoach #NeuroplasticityTraining #FitnessMotivation #AwarenessIsStep1 #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #InnerVoice""",

"""The summer food freedom framework. 🍉

BBQs. Birthday parties. Pool days. Vacations. The moments most plans fall apart.

Here's how Atomic Summer handles it:

BEFORE the event: Eat a protein-forward meal. Don't show up hungry.

AT the event: Choose one indulgence you'll genuinely enjoy — and enjoy it FULLY. No guilt.

AFTER the event: Back to normal at the very NEXT meal. Not Monday. The next meal.

No rules about what you can eat. No tracking. Just intention before, enjoyment during, grace after.

THIS is how women in my community lose weight through summer. 💜

Save this. Share it with someone who needs it.

Day 13.

#AtomicSummer #Day13 #FoodFreedom #FitForExcellence #SummerEating #IntuitiveEating #FoodGuilt #NoMoreDiets #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FoodFreedom #HealthyMindset #BBQSeason #MindfulEating #WeightLossLifestyle #FitnessChallenge #CoachAmy #HealthyChoices""",

"""TWO WEEKS IN. 🎊

Most people who start a fitness program quit in the first two weeks.

YOU DIDN'T.

Write down 3 things that have already changed since Day 1:

1. ___________
2. ___________
3. ___________

Maybe it's energy. Sleep. How you talk to yourself. How proud you feel.

The scale is ONE measurement. Not the most important one.

Tag a friend who's doing Atomic Summer with you! Let's celebrate. 💜

#AtomicSummer #TwoWeeks #FitForExcellence #NonScaleVictory #Progress #2Weeks #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FitnessJourney #NSV #FitnessMotivation #WomensFitness #HabitFormation #Milestone #BodyTransformation #HealthyLifestyle #CoachAmy #WomenSupportingWomen""",

# ── CHALLENGE: Days 15–21 (July 20–26) WEEK 3 ───────────────────────────────
"""The protein secret most women don't know. 🥚

When you eat enough protein:
✅ Hunger drops
✅ Cravings reduce
✅ Muscle stays when you lose weight
✅ Energy stays stable all day

Atomic Summer protein goal: 25–30g at EVERY meal.

That looks like:
→ 4 eggs
→ 1 cup Greek yogurt
→ 4 oz chicken
→ A protein shake
→ A can of tuna

No calorie counting. Just make sure every meal has a solid protein source.

Watch what happens. 💜

Day 15.

#AtomicSummer #Day15 #ProteinTips #FitForExcellence #NutritionAdvice #ProteinGoals #WeightLoss #FitOver40 #WomenOver40 #HighProteinDiet #NutritionCoach #SummerNutrition #WomensWellness #FitnessMotivation #MuscleBuilding #FatLoss #HealthyEating #WomensFitness #MidlifeWellness #CoachAmy""",

"""Fiber — your secret weapon for weight loss. ⚡

Here's something wild: your body makes its OWN GLP-1 naturally. And fiber is what triggers it.

Fiber → slows digestion → keeps you full → balances blood sugar → reduces cravings.

Top fiber sources to add this week:
🌱 Chia seeds in your morning smoothie
🥙 Lentils or beans at lunch
🫐 Berries instead of processed snacks
🥑 Avocado — most satisfying food on the planet

Protein + fiber at every meal = the Atomic Summer nutrition foundation.

Simple. Sustainable. IT WORKS. 💜

Save this and share it with someone who needs it!

Day 16.

#AtomicSummer #Day16 #FiberGuide #FitForExcellence #GLP1Natural #GLP1 #FiberFoods #WeightLoss #NutritionTips #FitOver40 #WomenOver40 #NaturalGLP1 #BloodSugar #CravingControl #NutritionCoach #SummerNutrition #WomensWellness #HealthyEating #FatLoss #CoachAmy""",

"""This one change can STOP cravings. 💧

Most afternoon cravings — especially for sweets — are actually DEHYDRATION signals.

Your body asks for water. Your brain hears "sugar."

Atomic Summer hydration goal: 80–100oz of water daily.

Here's how to make it automatic:
☀️ 20oz before coffee (morning)
🌤️ 20oz before lunch
🌥️ 20oz mid-afternoon when cravings hit
🌙 20oz before dinner

Next time you want something sweet at 3pm — drink 20oz first. Give it 15 min.

You might be surprised. 💜

Save this schedule. Try it tomorrow.

Day 17 of Atomic Summer.

#AtomicSummer #Day17 #Hydration #CravingControl #FitForExcellence #WaterGoals #DrinkMoreWater #CravingsGone #WeightLoss #FitOver40 #WomenOver40 #HydrationTips #NutritionCoach #SummerWellness #WomensWellness #FatLoss #HealthyHabits #FitnessMotivation #CoachAmy #HydrationChallenge""",

"""The most underrated fitness tool: SLEEP 😴

Poor sleep is one of the biggest drivers of weight gain — and almost nobody talks about it.

When you don't sleep enough:
⬆️ Cortisol rises
⬆️ Hunger hormones spike
⬇️ Willpower drops
🔒 Body holds onto fat

One bad night of sleep can make the next day feel like an uphill battle against your own cravings.

This week's challenge: go to bed 30 minutes earlier. Dark room. No phone.

Sleep is when your body repairs the muscle you built today. When your hormones reset. When tomorrow's willpower gets recharged.

Prioritize it. 💜

Save this. Share it. Day 18.

#AtomicSummer #Day18 #SleepTips #FitForExcellence #HormoneHealth #BetterSleep #SleepAndWeightLoss #Cortisol #HormoneBalance #FitOver40 #WomenOver40 #MidlifeWellness #SleepHealth #FitnessMotivation #WeightLoss #WomensWellness #FatLoss #RecoverySleep #CoachAmy #MenopauseSleep""",

"""Week 3 is where DRIFT happens — not on your watch. 🌊

The excitement of Day 1 has worn off. The finish line still feels far. Life is busy.

This is the moment most people quietly go quiet. Not on purpose. Just... life.

I'm posting this because I DON'T want that to be you.

You've invested 19 days in yourself. That's not nothing. That's a FOUNDATION.

Today I'm asking you to recommit. Not forever. Just for today. Just this one workout.

"I choose myself today."

Say it. Mean it. Go. 💜

Drop a 💜 if you're still showing up!

#AtomicSummer #Day19 #NoDrift #FitForExcellence #StillGoing #Week3 #Recommit #FitnessMotivation #WomensWellness #FitOver40 #WomenOver40 #ConsistencyWins #FitnessChallenge #ShowUp #MidweekMotivation #WomensFitness #GrowthMindset #ChooseYourself #CoachAmy #NeverQuit""",

"""Emotional eating — the real fix. 🧘‍♀️

Stress eating isn't a willpower problem. Full stop.

It's a coping mechanism. And a very human one.

Food gives comfort, pleasure, and relief. There's nothing wrong with your brain for wanting it when you're overwhelmed.

The fix isn't to white-knuckle past it.

The fix is a SECOND TOOL in your kit.

When the urge hits:
⏸️ Pause 5 seconds
💭 Name what you're actually feeling (stressed, lonely, bored, tired)
❓ Ask: "What does THIS feeling actually need right now?"

Sometimes it's water. Sometimes a walk. Sometimes a call to a friend.

And sometimes it's still the food — and that's okay. You choose CONSCIOUSLY. 💜

Save this. Day 20.

#AtomicSummer #Day20 #EmotionalEating #FitForExcellence #SelfCare #StressEating #EmotionalEatingRecovery #FoodFreedom #WomensWellness #FitOver40 #WomenOver40 #MindfulEating #SelfCompassion #FitnessMotivation #MindsetCoach #WomensFitness #HealthyMindset #FoodRelationship #CoachAmy #IntuitiveLiving""",

"""21 days. That's a habit forming. 🌟

Research shows it takes 21–66 days to form a new habit. You just hit the first milestone.

Something is already different about you — whether you feel it fully or not.

Your brain has started to build new pathways.
Your body has started to expect the movement.
Your identity is slowly, quietly shifting.

Write this down today:

"I am not the same woman I was 21 days ago."

You're not. 💜

Tag someone who's in Atomic Summer with you! Three more weeks of THIS. Let's go.

#AtomicSummer #Day21 #3WeeksStrong #HabitForming #FitForExcellence #21Days #HabitFormation #NeuroplasticityTraining #FitOver40 #WomenOver40 #WomensWellness #FitnessMotivation #IdentityShift #Milestone #NewHabit #FitnessJourney #WomensFitness #GrowthMindset #CoachAmy #YouAreChanging""",

# ── CHALLENGE: Days 22–28 (July 27 – Aug 2) WEEK 4 ──────────────────────────
"""Consistency ≠ Perfection. 📅

I'll say it again because most women confuse these two and it costs them everything.

CONSISTENCY: Show up most days. Do something most of the time. Never miss twice.

PERFECTION: Do it exactly right every time — and feel like a failure when you don't.

I'll tell you which one gets results:

CONSISTENCY. Every single time.

A woman who works out 5 days/week for a year beats a woman who works out every day for a month and quits. Every. Time.

Be consistent. Not perfect. 💜

Day 22 of Atomic Summer.

#AtomicSummer #Day22 #ConsistencyOverPerfection #FitForExcellence #Consistency #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #NoPerfection #HealthyHabits #SummerFitness #FitnessJourney #AtomicHabits #WomensFitness #GrowthMindset #HabitFormation #ShowUp #CoachAmy #FinishersMindset""",

"""Habit stacking — the easiest way to make it automatic. 🏗️

Instead of building a brand new routine from scratch, ATTACH your new habit to something you already do automatically.

Examples:
☕ After I pour my morning coffee → I drink 20oz of water first
🪥 After I brush my teeth → I say my identity statement
🚗 After I drop the kids off → I do my workout
🥗 After I sit down for lunch → I check my protein

The TRIGGER (existing habit) fires the new habit automatically.

Your brain loves this. It's efficient. It's sticky.

What's one habit you can STACK your workout onto? Tell me below 👇 💜

Save this. Day 23 of Atomic Summer.

#AtomicSummer #Day23 #HabitStacking #FitForExcellence #AtomicHabits #HabitFormation #TinyHabits #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #RoutineBuilding #MorningRoutine #HealthyHabits #WomensFitness #HabitChallenge #GrowthMindset #SummerFitness #CoachAmy #AutomaticHabits""",

"""Your environment shapes your behavior MORE than willpower does. 🏡

If chips are on the counter — you'll eat them.
If your workout clothes are out the night before — you'll put them on.
If your phone is in your bedroom — you'll scroll instead of sleep.

Three tweaks for this week:

1️⃣ Move snacks you don't want to eat to the BACK of the pantry
2️⃣ Set out your workout clothes tonight before bed
3️⃣ Put a water bottle somewhere you'll see it the moment you wake up

These feel tiny. They are MASSIVE.

Your future self is shaped by what your present self makes easy. 💜

Save this. Design your environment to WIN.

Day 24.

#AtomicSummer #Day24 #EnvironmentDesign #FitForExcellence #HabitTips #AtomicHabits #FrictionFree #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #DefaultEnvironment #HealthyHome #WomensFitness #HabitFormation #GrowthMindset #SummerFitness #CoachAmy #TinyChanges #BigResults""",

"""You weren't designed to do this alone. 🤝

Research shows people with accountability partners are 65% more likely to meet their goals.

With regular check-ins: 95%.

You have this community. You have me. USE IT.

Tag your Atomic Summer accountability partner below 👇

And if you haven't been checking in — I notice. I care. Drop a 💜 in the comments and tell me how you're REALLY doing.

Day 25. 💜

#AtomicSummer #Day25 #Accountability #FitForExcellence #WomenSupportingWomen #AccountabilityPartner #FitnessMotivation #WomensWellness #FitOver40 #WomenOver40 #CommunityLove #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #FitnessChallenge #CheckIn #YouAreNotAlone #WomenLiftingWomen""",

"""Had a hard week? Here's what to do. 🌧️

Maybe you missed a few days. Had an event that threw you off. Got sick.

Here's the only thing that matters right now:

Are you BACK?

Because the comeback is more important than the fall.

The women who finish Atomic Summer aren't the ones who never slipped — they're the ones who slipped and came back THE NEXT DAY.

If you're reading this post, you haven't given up. That means you're still in.

"I don't need a perfect record. I need a comeback story." 💜

Drop a 💪 if you're back.

#AtomicSummer #Day26 #Comeback #FitForExcellence #NeverGiveUp #ComebackStory #FitnessMotivation #WomensWellness #FitOver40 #WomenOver40 #Resilience #NeverMissTwice #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #GetBackUp #NotDone #YouveGotThis""",

"""Your body is changing — here's the REAL proof. 📊

Forget the scale for a second.

Check THESE non-scale victories:

✅ Are you sleeping better?
✅ Is your afternoon energy higher?
✅ Are your clothes fitting differently?
✅ Has the food noise in your head gotten quieter?
✅ Do you feel more PROUD of yourself than 27 days ago?

ANY yes on that list is a real result.

Your body is changing in ways a scale can't measure.

Honor the full picture. 💜

Day 27. What's YOUR non-scale victory this week? Drop it below 👇

#AtomicSummer #Day27 #NonScaleVictory #FitForExcellence #Progress #NSV #FitnessJourney #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #ScaleDontLie #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #RealResults #BodyTransformation #WomenSupportingWomen #YouAreChanging""",

"""FOUR WEEKS. HALFWAY THERE. 🏁

Four weeks ago you made a decision. You chose yourself.

And you have shown up — imperfectly, messily, through busy days and hard days and days you didn't feel like it.

You. Kept. Going.

THAT is the transformation. Not just the weight or the inches — the identity shift happening every single day.

You are becoming her. I can see it from here.

Four more weeks. Let's finish what we started. 💜

Tag a friend who's doing Atomic Summer — let them know you see them! 🙌

#AtomicSummer #FourWeeks #HalfwayThere #FitForExcellence #Transformation #4Weeks #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #HabitFormation #IdentityShift #Milestone #CoachAmy #WomenSupportingWomen #BodyTransformation""",

# ── CHALLENGE: Days 29–35 (Aug 3–9) WEEK 5 ──────────────────────────────────
"""On vacation? Here's the plan. ✈️

Vacation doesn't have to derail you.

Pick ONE non-negotiable + give yourself grace on everything else.

Your one non-negotiable: 10 minutes of movement. Every day. No matter what.

A walk on the beach counts.
Hotel room yoga counts.
Dancing at the family reunion counts.

One habit that's small enough to SURVIVE ANYTHING — that's how it stays alive through vacation.

Everything else: give yourself full grace. You're on vacation. Live your life. 💜

Come back home and pick right back up at the next meal.

Day 29 of Atomic Summer. 🌴

#AtomicSummer #Day29 #VacationFitness #FitForExcellence #TravelFit #VacationWorkout #FitnessOnVacation #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #SummerVacation #TravelFitness #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #BeachWorkout #NeverStop""",

"""30 days. Let me tell you what nobody talks about. 🌟

At the 30-day mark, women in my community often say:

"I don't know why, but I just feel different."

They're not always down a massive amount of weight. But they're:

😴 Sleeping better
🧠 Making better decisions without trying
💬 Saying kinder things to themselves without thinking about it
😌 Feeling less controlled by food

That's the self-talk rewire happening in REAL TIME.

Your brain has been changing for 30 days. The body follows the brain.

Stay the course. 💜

Day 30 of Atomic Summer!

#AtomicSummer #Day30 #30Days #FitForExcellence #MindBodyConnection #30DayMilestone #SelfTalkRewire #FitOver40 #WomenOver40 #WomensWellness #FitnessMotivation #Neuroplasticity #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #BrainChange #BodyFollowsBrain #YouAreTransforming""",

"""What to do when motivation disappears. 🔋

Motivation is gone today? GOOD.

Learning to show up when you're NOT motivated is the most important skill you can build.

Motivation is a feeling.
Discipline is a decision.
Identity is who you ARE.

When motivation disappears, fall back on identity:

"I'm the kind of woman who shows up for herself — especially when she doesn't feel like it."

Then do the MINIMUM. 10 minutes. One set. A walk around the block.

Something that proves the identity true.

The bar on no-motivation days is on the floor. You just have to step over it. 💜

Save this for your next hard day. Day 31.

#AtomicSummer #Day31 #NoMotivation #FitForExcellence #DisciplineOverMotivation #MotivationVsDiscipline #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #IdentityBasedHabits #ShowUp #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #JustDoIt #MinimumViableWorkout #FinishersMindset""",

"""Stop comparing. This is YOUR lane. 🚫

Her results are NOT your timeline.

Every transformation you see on social media is months or years in the making — with good lighting, a good angle, and very selective timing.

The woman next to you in this challenge who's down 10 lbs might have 20 years of failed diets behind that success. You don't know her whole story.

Your only competition: the version of you from YESTERDAY.

And based on the fact that you're still here on Day 32?

You're winning that race. 💜

#AtomicSummer #Day32 #ComparisonTrap #FitForExcellence #YourLane #StayInYourLane #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #CompareNoMore #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #YourJourney #SocialMediaTruth #YouAreEnough #CompetingWithYesterday""",

"""Why EVERY woman over 35 needs strength training. 💪

Especially during perimenopause and menopause.

Here's why:

🦴 Builds bone density (critical as estrogen drops)
🔥 Increases metabolism (muscle burns fat at rest)
🍬 Improves insulin sensitivity (reduces belly fat storage)
💪 Builds the confidence that cardio alone never will

You don't need heavy weights. You don't need a gym.

You need CONSISTENCY — and the workouts in Fit Plus are built exactly for this.

Save this. Share it with a woman who needs to hear it. 💜

Day 33 of Atomic Summer.

#AtomicSummer #Day33 #StrengthTraining #Menopause #FitForExcellence #StrengthTrainingForWomen #Over35Fitness #FitOver40 #WomenOver40 #Perimenopause #MenopauseHealth #BoneDensity #MetabolismBoost #WomensWellness #FitnessMotivation #HormoneHealth #MidlifeWellness #WomensFitness #CoachAmy #StrongerEveryDay""",

"""Who knows you're doing this challenge? 👯‍♀️

Studies show people who share their goals are significantly more likely to follow through.

Not because of judgment — because of IDENTITY.

When others know → your brain doubles down on protecting who you said you are.

Today: tell one person you're doing Atomic Summer.

Better yet — if you know someone who would benefit from this, TAG THEM BELOW. 💜

She might be sitting in her car right now listening to the inner voice that says she can't change.

You could be the reason she tries.

Day 34.

#AtomicSummer #Day34 #TagAFriend #FitForExcellence #WomenLiftingWomen #ShareYourGoals #Accountability #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #WomenSupportingWomen #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #TagSomeone #SpreadTheGoodness #YouCouldBeHerReason""",

"""5 WEEKS IN. You are NOT the same woman who started. 🦋

Think about the woman who started July 6.

What was she struggling with?
What was she afraid of?
What did she tell herself about why she couldn't do this?

Now look at you. Still here. Day 35. Still showing up.

The internal shift that's happened in 35 days is bigger than any number on a scale.

You've proven something to yourself that no one can take away.

Three more weeks. This is where the REAL momentum builds.

Let's finish strong. 💜

#AtomicSummer #FiveWeeks #FitForExcellence #StillGoing #Transformation #5Weeks #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #IdentityShift #Milestone #CoachAmy #YouAreTransforming #WomenSupportingWomen #BodyTransformation""",

# ── CHALLENGE: Days 36–42 (Aug 10–16) WEEK 6 ────────────────────────────────
"""Your habit is becoming AUTOMATIC. 🔬

After 36 days of consistent action, your brain has started creating what scientists call automatic behavior patterns.

The habit is starting to run on autopilot.

This is why long-time exercisers don't feel like they "have" to work out. It's not willpower. It's WIRING.

You're building that wiring right now. Every rep, every walk, every workout you did when you didn't want to — all of it is laying new neural pathways.

You're not just getting fit. You're REPROGRAMMING. 🧠💜

Day 36 of Atomic Summer.

#AtomicSummer #Day36 #HabitScience #FitForExcellence #Automatic #NeuralPathways #Neuroplasticity #HabitFormation #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #AtomicHabits #AutoPilot #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #BrainWiring""",

""""I'll do it after dinner."

How many times has that sentence cost you a workout? 🕐

Here's what I know: the workout you put off until later is the workout that doesn't happen. Not because you're lazy — because LATER brings new obstacles, new exhaustion, new reasons.

Today's challenge: do your workout FIRST.

Before email. Before social media. Before the to-do list.

Schedule it like a meeting you cannot cancel — because you can't. You have a commitment to yourself. 💜

Day 37. First thing. Go.

#AtomicSummer #Day37 #DoItFirst #FitForExcellence #MorningWorkout #MorningRoutine #DoItEarly #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #NoExcuses #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #WorkoutFirst #ScheduleIt #WinTheMorning""",

"""Menopause and metabolism — the truth. 🔥

Your body is NOT betraying you. It's shifting. And understanding the shift changes everything.

As estrogen drops:
→ Fat redistributes (especially to the midsection)
→ Metabolism slows
→ Sleep quality decreases
→ The approach that worked at 30 may not work at 50

What ACTUALLY works:
✅ Strength training 3x/week — non-negotiable
✅ Protein at every meal — prevents muscle loss
✅ Stress reduction — cortisol and estrogen are connected
✅ Self-talk work — the mindset piece matters MORE at this stage, not less

You're in the right program. 💜

Save this and share it with every woman over 40 you know.

Day 38.

#AtomicSummer #Day38 #Menopause #HormoneHealth #FitForExcellence #MenopauseFitness #Perimenopause #MidlifeWellness #MenopauseWeightLoss #FitOver40 #WomenOver40 #HormoneBalance #EstrogenDrop #StrengthTraining #MetabolismBoost #WomensWellness #FitnessMotivation #MidlifeHealth #CoachAmy #MenopauseSupport""",

"""Take a photo today. 📸

I know. Nobody loves this.

But here's the thing: photos capture the truth in a way your eyes can't when you're looking in the mirror every day.

You've been changing so gradually that your brain normalizes it.

A photo from Day 1 next to one from today will show you something the scale and the mirror miss.

Take it. Save it. You don't have to share it with anyone.

But on August 30 when this is over — you'll want proof of how far you came. 💜

Day 39 of Atomic Summer.

#AtomicSummer #Day39 #ProgressPhoto #FitForExcellence #Transformation #ProgressPics #BeforeAndAfter #FitnessJourney #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #ProofOfChange #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #BodyTransformation #DocumentYourJourney #YourStory""",

"""40 DAYS IN. Let me count your real wins. 🏆

✅ 40 days you chose yourself over excuses
✅ 40 days of building a habit that's nearly automatic
✅ 40 days of practicing a kinder inner voice
✅ 40 days of proving the story wrong — the one that said you always quit

Whatever the scale says — 40 consecutive days of commitment is RARE.

Most people will never experience it.

You are not most people. 💜

Drop a 🏆 in the comments so I can see who's still here!

#AtomicSummer #Day40 #40Days #FitForExcellence #RealWins #40DayMilestone #FitnessJourney #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #IdentityShift #HabitFormation #WomensFitness #Milestone #SummerFitness #CoachAmy #RareHuman #ConsistencyWins #YouAreExtraordinary""",

"""August 30 is not the end. It's a beginning. 🗓️

I want to start talking about what happens AFTER Atomic Summer — because the worst thing that can happen is you finish and drift back to where you were.

The habit you've built over these 41 days is yours. The self-talk practice. The identity. The routine.

Those don't expire on August 30.

Fit Plus continues beyond the challenge. For women who want to keep going with accountability, daily workouts, and coaching — it's here.

But even if you stop — the version of yourself you've BECOME is permanent.

That's yours forever. 💜

Day 41. Link in bio for Fit Plus.

#AtomicSummer #Day41 #FitPlus #FitForExcellence #KeepGoing #WhatComesNext #LifestyleChange #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #LifetimeHabit #IdentityShift #PermanentChange #NotJustAChallenge""",

"""SIX WEEKS. Extraordinary. ⭐

Six weeks ago you made a decision.

Extra-ordinary. Beyond ordinary.

Most people live their whole lives intending to change and never doing it for SIX consecutive weeks.

You just did.

Two more weeks. The final stretch.

This is where people either FINISH STRONG or let the finish line make them complacent.

Not you. You finish what you start. You've been proving that for 42 days.

Let's end this summer differently than every summer before. 💜

#AtomicSummer #SixWeeks #FitForExcellence #AlmostThere #FinishStrong #6Weeks #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #Milestone #CoachAmy #Extraordinary #TwoMoreWeeks #FinalStretch #YouAreAmazing""",

# ── CHALLENGE: Days 43–49 (Aug 17–23) WEEK 7 ────────────────────────────────
"""11 days left. This is where champions separate. 🏃‍♀️

Most people COAST in the final stretch. They figure they've done enough. They ease up just when the compound effect is about to pay off the most.

Don't be most people.

The last two weeks of any commitment are where the transformation SOLIDIFIES.

The habit that's been forming for 43 days is about to become fully automatic — but only if you don't take your foot off the gas.

These last 11 days? Show up like it's Day 1. With the energy of the beginning. With the wisdom of 43 days behind you.

Let's finish this. 💜

Day 43.

#AtomicSummer #Day43 #FinalStretch #FitForExcellence #FinishLine #11DaysLeft #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #Champions #DontCoast #CompoundEffect #FinalWeeks #GoHard""",

"""Your self-talk at the finish line — compare it to Day 1. 🎤

On Day 1, what did you tell yourself?

Maybe: "I hope I can stick with this."
Maybe: "I always quit eventually."
Maybe: "We'll see if this one is different."

What do you tell yourself NOW?

Even if it's not perfect — I bet it's different. A little quieter in the doubt. A little louder in the belief.

That shift is the WHOLE POINT.

Every workout you completed, every time you got back up — you were adding evidence to a new story about who you are.

Keep adding. 10 more days. 💜

Drop your Day 1 vs. now self-talk below 👇

Day 44.

#AtomicSummer #Day44 #SelfTalk #FitForExcellence #NewStory #SelfTalkEvolution #SelfTalkTrainer #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #InnerVoice #NewBelief #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #YouAreChanging #MindsetShift""",

"""45 days of evidence. 🦁

You've had every excuse available to you.

Busy schedule. Summer chaos. Hard days. Low energy. Events. Vacations. LIFE.

And you're still here.

45 data points that prove your inner critic wrong:

❌ "You always quit." → WRONG. 45 days.
❌ "You can't stick to things." → WRONG. 45 days.
❌ "This isn't working." → WRONG. Look at you. 45 DAYS.

You've outworked your excuses. 💜

Day 45. Drop a 💪 if you're still going!

#AtomicSummer #Day45 #OutworkedExcuses #FitForExcellence #45Days #EvidenceBasedIdentity #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #InnerCriticSilenced #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #YouProvedItWrong #45DaysStrong #IdentityShift #YouAreStrong""",

"""They're watching. 👨‍👩‍👧

Every time you lace up your shoes.
Every time you choose a nourishing meal.
Every time you get back up after a hard day.

Your kids, your partner, your family — they see it.

And they're learning that taking care of yourself is IMPORTANT. That you're worth the effort. That consistency is possible.

You're not just transforming yourself. You're MODELING something for everyone in your life.

That's the ripple effect of Atomic Summer. It doesn't stop with you. 💜

Tag someone in your life you're doing this for.

Day 46.

#AtomicSummer #Day46 #RippleEffect #FitForExcellence #RoleModel #MomLife #YouAreWatched #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FamilyFirst #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #ModelingBehavior #MomGoals #LeadByExample""",

"""4 days from the final week. 💥

Think about the hardest day you had in this challenge.

The day you almost didn't show up. The day you missed and had to come back. The day everything felt hard.

You survived that day. You came back.

And now you're 4 days from the final week.

Every hard day was PRACTICE for this. You've been building resilience, grit, identity — and now it's time to use all of it.

Go hard these last 4 days. Give August everything you've got. 💜

Day 47.

#AtomicSummer #Day47 #FinalPush #FitForExcellence #Last4Days #YouCameBack #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #Resilience #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #GoHard #AlmostThere #FinishLine #BuildingGrit""",

"""Write a letter to yourself. 📝

From the woman who started July 6. To the woman who will cross the finish line on August 30.

What do you want her to know?
What are you proud of?
What shifted?
What surprised you?

Write it now — before you finish — because the perspective changes the moment you cross that line.

Share it in the comments or keep it for yourself. Either way: write it.

Your story deserves to be told — especially by you. 💜

Day 48.

#AtomicSummer #Day48 #LetterToSelf #FitForExcellence #YourStory #JournalPrompt #SelfReflection #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #WriteItDown #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #YourTransformation #SelfDiscovery #YouDeserveThisStory""",

"""SEVEN WEEKS DONE. ONE WEEK TO GO. 🌅

49 days ago you decided to bet on yourself.

And every single day since, you've put your chips on the table.

Tomorrow begins the FINAL WEEK of Atomic Summer.

I want you to feel this moment. Not rush past it to the finish line.

One week. Let's make it count. 💜

Drop a 💜 if you're here for the final week! I want to see who's crossing that finish line with me.

#AtomicSummer #SevenWeeks #FinalWeek #FitForExcellence #OneWeekLeft #7Weeks #SummerFitness #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #Milestone #CoachAmy #AlmostThere #FinishStrong #LastWeek #FinalCountdown""",

# ── CHALLENGE: Days 50–56 (Aug 24–30) WEEK 8 ────────────────────────────────
"""THE FINAL 7 DAYS. THIS IS IT. 🌟

50 days in. 7 to go.

This final week I want you to go ALL IN.

Not because you have to prove something. Because you've already proven it.

But because finishing STRONG is its own reward.

The woman who coasts across the finish line and the woman who SPRINTS across it feel very different on August 31.

One feels like she got by. One feels like she EARNED it.

You've earned 50 days. Earn the last 7 the same way. 💜

Drop a 🔥 to show me you're in for the final push!

#AtomicSummer #Day50 #FinalWeek #FitForExcellence #Sprint #FinalPush #7DaysLeft #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #FinishStrong #SprintToTheEnd #LastWeek #GiveItAll""",

"""The identity you've built is PERMANENT. 💎

The woman who shows up, who takes care of herself, who gets back up — that doesn't disappear on August 30.

You BUILT her. She's yours.

Habits can be interrupted. Life gets in the way.

But the BELIEF that you're capable? The evidence that you can do hard things? The self-trust that comes from 51 days of keeping your word to yourself?

That's permanent.

Nobody can take that from you. 💜

Day 51. 5 days to go.

#AtomicSummer #Day51 #PermanentIdentity #FitForExcellence #SelfTrust #YouBuiltHer #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #IdentityShift #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #SelfBelief #IdentityBasedHabits #YouAreStrong #ForeverChanged""",

"""What's your ONE takeaway from Atomic Summer? 💡

If you could carry ONE thing forward from these 6 weeks — what would it be?

The never-miss-twice rule?
The identity statement?
A specific workout you now love?
The self-talk shift?
Just the proof that you CAN do this?

Whatever it is — write it down. Make it concrete. Keep it.

This challenge ends in 4 days. But the thing you LEARNED? That lives forever. 💜

Drop your #1 takeaway below 👇 I want to hear it!

Day 52.

#AtomicSummer #Day52 #Takeaway #FitForExcellence #Lessons #WhatDidYouLearn #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #Reflection #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #CarryItForward #TransformationLessons #LifeChanged #KeepThis""",

"""THREE DAYS LEFT. 🏅

You are three days away from doing something most people only talk about.

Finishing an 6-week commitment to yourself is rare. Not because it's impossible — but because most people quit before they get here.

You didn't quit. You're THREE DAYS AWAY.

When you cross the finish line, the feeling isn't just relief.

It's self-respect. It's trust. It's knowing in your bones that when you decide to do something — you DO it.

Three more days to feel it. 💜

Day 53.

#AtomicSummer #Day53 #AlmostThere #FitForExcellence #3DaysLeft #ThreeDays #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #SelfRespect #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #FinishLine #YouCantQuitNow #Rare #AlmostDone""",

"""TWO MORE DAYS. Don't slow down now. 🌈

The finish line is so close you can see it.

Don't do what most people do at the end of a race — don't slow down to look at the crowd.

Keep your eyes forward and RUN THROUGH THE TAPE.

Two more workouts. Two more days of showing up. Two more days of the woman you've become.

You started this because you were done starting over every summer.

You're about to prove you did something different this time. 💜

Day 54.

#AtomicSummer #Day54 #TwoDaysLeft #FitForExcellence #RunThroughTheTape #TwoDays #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #NoSlowing #EyesForward #AlmostThere #FinishStrong #YouDidSomethingDifferent""",

"""TOMORROW IS THE LAST DAY. 🌙

I want you to go to sleep tonight feeling PROUD.

Not because everything was perfect. Not because you never slipped or had a hard week.

But because you came back EVERY SINGLE TIME.

55 days of choosing yourself. 55 days of building something real.

Tomorrow we finish.

Say this before you sleep tonight: "I am a woman who finishes what she starts." 💜

Day 55. See you at the finish line tomorrow.

#AtomicSummer #Day55 #LastNight #FitForExcellence #OneMoreDay #Tomorrow #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #ProudOfYou #FitnessJourney #WomensFitness #GrowthMindset #SummerFitness #CoachAmy #LastNight #FinishLine #SheFinishes #55Days""",

"""YOU DID IT. 🎉🏆💜

AUGUST 30. ATOMIC SUMMER IS COMPLETE.

56 days. 6 weeks. July 6 to August 30.

YOU. DID. IT.

I am so proud of you I could cry. Not because of how you look — but because of WHO YOU BECAME.

You are no longer the woman who starts on Monday.
You are no longer the woman who says she'll try.
You are the woman who DID.

The habit is real. The identity is real. The transformation is real.

If you want to keep this momentum going — Fit Plus is waiting for you. Link in bio. 💜

And if you need a rest — take it. You earned it.

But whatever you do: remember who you proved yourself to be this summer. Don't let her go.

CONGRATULATIONS, Atomic Summer champion. 🏆

Let's Get Fit! — Coach Amy 💜

#AtomicSummer #IFinished #FitForExcellence #AtomicSummerComplete #Transformation #FitnessChallenge #SheFinished #WomensWellness #FitOver40 #WomenOver40 #FitnessMotivation #FitnessJourney #WomensFitness #GrowthMindset #Congratulations #CoachAmy #6WeekChallenge #BodyTransformation #YouDidIt #AtomicSummerChampion""",
]

# ── API HELPERS ───────────────────────────────────────────────────────────────
def _multipart_body(fields, file_field, file_path, mime_type):
    """Build a multipart/form-data body. Returns (boundary, body_bytes)."""
    import uuid
    boundary  = uuid.uuid4().hex
    parts     = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        )
    with open(file_path, "rb") as f:
        file_data = f.read()
    filename = os.path.basename(file_path)
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    )
    body = "".join(parts).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    return boundary, body

def upload_photo(image_path):
    """
    Upload a local image to the FB page photo library (unpublished).
    Returns (photo_id, public_cdn_url) — both needed for the two-for-one trick:
      • photo_id  → attach to the FB feed post
      • cdn_url   → pass to Instagram Content Publishing API (no second upload needed)
    """
    if not os.path.exists(image_path):
        return None, None
    import mimetypes
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    boundary, body = _multipart_body(
        {"access_token": PAGE_TOKEN, "published": "false"},
        "source", image_path, mime_type
    )
    req = urllib.request.Request(
        f"{BASE}/{PAGE_ID}/photos", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            photo_id = json.loads(r.read()).get("id")
        if not photo_id:
            return None, None
        # Fetch the public CDN URL from Facebook so Instagram can use it
        cdn_url = get_photo_url(photo_id)
        return photo_id, cdn_url
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"    Photo upload error: {err.get('error',{}).get('message','')[:80]}")
        return None, None

def get_photo_url(photo_id):
    """
    After uploading a photo to FB, fetch its public CDN URL.
    Returns the largest available image URL, or None.
    """
    params = urllib.parse.urlencode({
        "fields":       "images",
        "access_token": PAGE_TOKEN,
    })
    req = urllib.request.Request(f"{BASE}/{photo_id}?{params}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data   = json.loads(r.read())
            images = data.get("images", [])
            if images:
                # images are ordered largest → smallest
                return images[0].get("source")
    except Exception:
        pass
    return None

def schedule_ig_post(caption, image_url, scheduled_unix):
    """
    Schedule an Instagram post using the Content Publishing API.
    Uses the FB-hosted CDN URL so no second upload is needed.

    Flow for SCHEDULED posts (scheduled_unix is set):
      POST /{ig-user-id}/media with published=false + scheduled_publish_time
      → IG queues the post; no media_publish call needed.

    Flow for IMMEDIATE posts (scheduled_unix is None):
      POST /{ig-user-id}/media  → get container_id
      POST /{ig-user-id}/media_publish with creation_id  → goes live now

    Returns (container_id, success).
    Requires: instagram_content_publish + instagram_basic permissions on the token.
    """
    if not image_url:
        return None, False

    # Build container payload
    data = {
        "image_url":    image_url,
        "caption":      caption,
        "media_type":   "IMAGE",
        "access_token": PAGE_TOKEN,
    }
    if scheduled_unix:
        # Scheduled: tell IG not to publish yet and when to go live
        data["published"]              = "false"
        data["scheduled_publish_time"] = str(scheduled_unix)

    payload = urllib.parse.urlencode(data).encode()
    req     = urllib.request.Request(
        f"{BASE}/{IG_ID}/media", data=payload, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            container_id = json.loads(r.read()).get("id")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"    IG container error: {err.get('error',{}).get('message','')[:80]}")
        return None, False

    if not container_id:
        return None, False

    # Scheduled posts: container creation IS the schedule — done.
    if scheduled_unix:
        return container_id, True

    # Immediate posts only: fire media_publish to go live now
    pub_data    = {"creation_id": container_id, "access_token": PAGE_TOKEN}
    pub_payload = urllib.parse.urlencode(pub_data).encode()
    pub_req     = urllib.request.Request(
        f"{BASE}/{IG_ID}/media_publish", data=pub_payload, method="POST"
    )
    try:
        with urllib.request.urlopen(pub_req, timeout=20) as r:
            result     = json.loads(r.read())
            ig_post_id = result.get("id")
            return ig_post_id, bool(ig_post_id)
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"    IG publish error: {err.get('error',{}).get('message','')[:80]}")
        return None, False

def upload_video(video_path, title="Atomic Summer", scheduled_unix=None, description=""):
    """
    Upload a local video as a FB page video post.
    For scheduled videos, published=false + scheduled_publish_time.
    Returns (video_id, success).
    Facebook video uploads can be slow — timeout set to 5 min.
    """
    if not os.path.exists(video_path):
        print(f"    ⚠ Video not found: {video_path}")
        return None, False

    import mimetypes
    mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"
    fields = {
        "access_token":  PAGE_TOKEN,
        "title":         title,
        "description":   description,
        "published":     "false" if scheduled_unix else "true",
    }
    if scheduled_unix:
        fields["scheduled_publish_time"] = str(scheduled_unix)

    boundary, body = _multipart_body(fields, "source", video_path, mime_type)
    req = urllib.request.Request(
        f"https://graph-video.facebook.com/v25.0/{PAGE_ID}/videos",
        data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            result = json.loads(r.read())
            vid_id = result.get("id")
            return vid_id, bool(vid_id)
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"    Video upload error: {err.get('error',{}).get('message','')[:80]}")
        return None, False

# Posts that use the clouds video instead of a photo.
# These are pre-launch hype posts where a looping video background works well.
# Index is 0-based (post #1 = index 0).
VIDEO_POSTS = {0, 1, 2}   # Posts #1, #2, #3  — "Something big coming", "honest", "INTRODUCING"
VIDEO_FILE  = "video_clouds_bg.mov"

def post_and_schedule(message, scheduled_unix=None, image_filename=None):
    """
    THE TWO-FOR-ONE:
    1. Upload image to Facebook (hosted on FB CDN)
    2. Schedule the FB post with that image attached
    3. Grab the CDN URL from the uploaded photo
    4. Schedule the SAME image on Instagram using that URL — no second upload

    One image upload → both FB and IG scheduled simultaneously.

    For video posts (VIDEO_POSTS set), uploads to FB Videos endpoint only.
    Instagram video scheduling requires different handling (Reels API) —
    video posts currently schedule FB only; IG is text caption printed for manual posting.

    Returns: {"fb": fb_post_id, "ig": ig_post_id}
    """
    is_video  = image_filename and image_filename.endswith((".mov", ".mp4", ".avi", ".mkv"))
    photo_id  = None
    cdn_url   = None

    # ── VIDEO: FB only ───────────────────────────────────────────────────────
    if is_video:
        vid_path = os.path.join(IMAGES_DIR, image_filename)
        print(f"    📹 Uploading video... ", end="", flush=True)
        vid_id, ok = upload_video(vid_path, title=message[:60],
                                  scheduled_unix=scheduled_unix, description=message)
        if ok:
            print(f"✓ FB video scheduled  |  IG: manual post needed for video")
            return {"fb": vid_id, "ig": None}, True
        else:
            print("✗ video upload failed — posting text only")
            image_filename = None

    # ── PHOTO: upload once, use on both platforms ─────────────────────────────
    if image_filename:
        img_path = os.path.join(IMAGES_DIR, image_filename)
        if os.path.exists(img_path):
            print(f"    🖼 Uploading image... ", end="", flush=True)
            photo_id, cdn_url = upload_photo(img_path)
            if photo_id:
                print(f"✓  CDN URL: {'obtained' if cdn_url else 'not retrieved'}")
            else:
                print("✗ upload failed")
        else:
            print(f"    ⚠ Image not found: {img_path} (run download_assets.py first)")

    # ── SCHEDULE FACEBOOK POST ────────────────────────────────────────────────
    fb_data = {"message": message, "access_token": PAGE_TOKEN}
    if photo_id:
        fb_data["attached_media"] = json.dumps([{"media_fbid": photo_id}])
    if scheduled_unix:
        fb_data["published"]              = "false"
        fb_data["scheduled_publish_time"] = str(scheduled_unix)

    fb_payload = urllib.parse.urlencode(fb_data).encode()
    fb_req     = urllib.request.Request(
        f"{BASE}/{PAGE_ID}/feed", data=fb_payload, method="POST"
    )
    fb_post_id = None
    try:
        with urllib.request.urlopen(fb_req, timeout=20) as r:
            fb_post_id = json.loads(r.read()).get("id")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"    FB post error: {err.get('error',{}).get('message','')[:80]}")
        return {"fb": None, "ig": None}, False

    return {"fb": fb_post_id, "ig": None, "photo_id": photo_id}, bool(fb_post_id)

# ── PREVIEW MODE ──────────────────────────────────────────────────────────────
def show_preview():
    print("\n" + "="*70)
    print("ATOMIC SUMMER — All 67 Captions Preview")
    print("="*70)
    base = datetime(2026, 6, 25, tzinfo=timezone.utc)
    for i, cap in enumerate(CAPTIONS):
        day_date   = base + timedelta(days=i)
        slot_label = SLOT_LABELS[i % 4]
        label = (
            f"Pre-Launch #{i+1}" if i < 11
            else f"Day {i-10} (Challenge)"
        )
        print(f"\n── #{i+1} | {label} | {day_date.strftime('%b %d')} @ {slot_label} PDT ──")
        print(cap[:300] + ("..." if len(cap) > 300 else ""))
        print()
        if (i + 1) % 10 == 0:
            cont = input("Press Enter to continue (Q to quit)... ").strip()
            if cont.upper() == "Q":
                break

# ── POST NOW ──────────────────────────────────────────────────────────────────
def post_now(n):
    idx = n - 1
    if idx < 0 or idx >= len(CAPTIONS):
        print(f"Invalid post number. Choose 1–{len(CAPTIONS)}.")
        return
    cap      = CAPTIONS[idx]
    img_file = VIDEO_FILE if idx in VIDEO_POSTS else (IMAGE_MAP[idx] if idx < len(IMAGE_MAP) else None)
    print(f"\nPosting #{n} to Facebook NOW...")
    if img_file:
        media_path = os.path.join(IMAGES_DIR, img_file)
        media_type = "📹 Video" if img_file == VIDEO_FILE else "🖼 Image"
        found      = "✓ found" if os.path.exists(media_path) else "✗ NOT FOUND — run download_assets.py"
        print(f"{media_type}: {img_file} {found}")
    print(f"\n{cap[:200]}...\n")
    confirm = input("Confirm? (Y/N): ").strip().upper()
    if confirm != "Y":
        print("Cancelled.")
        return
    result, ok = post_and_schedule(cap, image_filename=img_file)
    if ok:
        print(f"✓ FB Posted! ID: {result.get('fb')}")
        if result.get("ig"):
            print(f"✓ IG Scheduled! ID: {result['ig']}")
    else:
        print(f"✗ Error posting.")

# ── SCHEDULE ALL ──────────────────────────────────────────────────────────────
def schedule_all():
    print(f"\nScheduling all {len(CAPTIONS)} Atomic Summer posts on Facebook + Instagram...")
    print("Times rotate: 11:30 AM / 12:30 PM / 2:00 PM / 6:00 PM PDT")
    print("Two-for-one: each image uploads once → scheduled on FB and IG simultaneously\n")
    base = datetime(2026, 6, 25, tzinfo=timezone.utc)
    created = 0
    failed  = 0

    ig_schedule = []

    for i, cap in enumerate(CAPTIONS):
        day_date   = base + timedelta(days=i)
        unix_time  = send_time_unix(day_date, i)
        slot_label = SLOT_LABELS[i % 4]
        label      = f"Pre-Launch #{i+1}" if i < 11 else f"Day {i-10}"
        img_file   = VIDEO_FILE if i in VIDEO_POSTS else (IMAGE_MAP[i] if i < len(IMAGE_MAP) else None)

        result, ok = post_and_schedule(cap, scheduled_unix=unix_time, image_filename=img_file)
        if ok:
            media_tag = " 📹 video" if img_file == VIDEO_FILE else (f" 🖼 {img_file[:20]}" if img_file else "")
            print(f"  ✓ #{i+1:02d} | {label:15} | {day_date.strftime('%b %d')} @ {slot_label} PDT{media_tag}")
            created += 1
        else:
            print(f"  ✗ #{i+1:02d} | {label:15} | FB FAILED")
            failed += 1

        # Build IG schedule entry — photo_id lets GitHub Actions fetch a fresh CDN URL later
        ig_schedule.append({
            "post_num":      i + 1,
            "label":         label,
            "scheduled_utc": datetime.fromtimestamp(unix_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "caption":       cap,
            "fb_photo_id":   (result or {}).get("photo_id"),
            "is_video":      i in VIDEO_POSTS,
        })

        time.sleep(0.5)

    # ── EXPORT ig_schedule.json ────────────────────────────────────────────────
    with open("ig_schedule.json", "w", encoding="utf-8") as f:
        json.dump(ig_schedule, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Done! FB scheduled: {created}   Failed: {failed}")
    print(f"ig_schedule.json written — commit it + ig_poster.py + .github/ to GitHub.")

# ── IG COPY MODE ──────────────────────────────────────────────────────────────
def ig_copy(n):
    idx = n - 1
    if idx < 0 or idx >= len(CAPTIONS):
        print(f"Invalid post number. Choose 1–{len(CAPTIONS)}.")
        return
    base = datetime(2026, 6, 25, tzinfo=timezone.utc)
    day_date   = base + timedelta(days=idx)
    slot_label = SLOT_LABELS[idx % 4]
    label      = f"Pre-Launch #{idx+1}" if idx < 11 else f"Day {idx-10}"

    print(f"\n{'='*70}")
    print(f"#{n} | {label} | {day_date.strftime('%B %d, %Y')} @ {slot_label} PDT")
    print(f"{'='*70}")
    print("\n📋 COPY THIS FOR INSTAGRAM:\n")
    print(CAPTIONS[idx])
    print(f"\n{'='*70}")
    print(f"Signup link (add to bio/stories): {SIGNUP_URL}")

# ── IG BATCH EXPORT ───────────────────────────────────────────────────────────
def export_ig(output_path="atomic_summer_ig_captions.txt"):
    base = datetime(2026, 6, 25, tzinfo=timezone.utc)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, cap in enumerate(CAPTIONS):
            day_date   = base + timedelta(days=i)
            slot_label = SLOT_LABELS[i % 4]
            label      = f"Pre-Launch #{i+1}" if i < 11 else f"Day {i-10}"
            f.write(f"{'='*70}\n")
            f.write(f"#{i+1} | {label} | {day_date.strftime('%B %d, %Y')} @ {slot_label} PDT\n")
            f.write(f"{'='*70}\n\n")
            f.write(cap)
            f.write("\n\n")
    print(f"✓ All 67 Instagram captions exported to: {output_path}")

# ── SCHEDULE IG ONLY (FB already done) ───────────────────────────────────────
def schedule_ig_only():
    """
    IG-only scheduling pass — uploads each image to FB to get a CDN URL,
    then schedules on Instagram. Does NOT touch any existing FB scheduled posts.
    Use this when FB posts are already scheduled but IG needs to be caught up.
    """
    print(f"\nScheduling all {len(CAPTIONS)} posts on Instagram only (FB untouched)...")
    print("Times rotate: 11:30 AM / 12:30 PM / 2:00 PM / 6:00 PM PDT\n")
    base    = datetime(2026, 6, 25, tzinfo=timezone.utc)
    created = 0
    failed  = 0
    skipped = 0

    for i, cap in enumerate(CAPTIONS):
        day_date   = base + timedelta(days=i)
        unix_time  = send_time_unix(day_date, i)
        slot_label = SLOT_LABELS[i % 4]
        label      = f"Pre-Launch #{i+1}" if i < 11 else f"Day {i-10}"
        img_file   = IMAGE_MAP[i] if i < len(IMAGE_MAP) else None

        # Skip video posts — IG Reels needs a separate flow
        if i in VIDEO_POSTS:
            print(f"  ⏭ #{i+1:02d} | {label:15} | skipped (video — manual IG post)")
            skipped += 1
            continue

        if not img_file:
            print(f"  ⚠ #{i+1:02d} | {label:15} | no image assigned — skipping")
            skipped += 1
            continue

        img_path = os.path.join(IMAGES_DIR, img_file)
        if not os.path.exists(img_path):
            print(f"  ⚠ #{i+1:02d} | {label:15} | image not found: {img_file}")
            skipped += 1
            continue

        # Upload image to FB CDN (unpublished) just to get the public URL for IG
        print(f"  🖼 #{i+1:02d} uploading image for CDN... ", end="", flush=True)
        photo_id, cdn_url = upload_photo(img_path)
        if not cdn_url:
            print(f"✗ CDN URL not retrieved")
            failed += 1
            continue
        print(f"✓  scheduling IG... ", end="", flush=True)

        ig_post_id, ig_ok = schedule_ig_post(cap, cdn_url, unix_time)
        if ig_ok:
            print(f"✓ {ig_post_id}")
            print(f"    ✓ #{i+1:02d} | {label:15} | {day_date.strftime('%b %d')} @ {slot_label} PDT | IG ✓")
            created += 1
        else:
            print(f"✗ failed")
            failed += 1

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Done!  IG scheduled: {created}  |  Failed: {failed}  |  Skipped: {skipped}")
    if skipped:
        print(f"  ({skipped} video posts need manual IG posting)")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        show_preview()

    elif args[0] == "--post" and len(args) > 1:
        post_now(int(args[1]))

    elif args[0] == "--schedule":
        confirm = input(f"Schedule all {len(CAPTIONS)} posts to Facebook? (Y/N): ").strip().upper()
        if confirm == "Y":
            schedule_all()
        else:
            print("Cancelled.")

    elif args[0] == "--schedule-ig":
        confirm = input(f"Schedule all {len(CAPTIONS)} posts to Instagram only (FB untouched)? (Y/N): ").strip().upper()
        if confirm == "Y":
            schedule_ig_only()
        else:
            print("Cancelled.")

    elif args[0] == "--ig" and len(args) > 1:
        ig_copy(int(args[1]))

    elif args[0] == "--export-ig":
        export_ig()

    else:
        print("""
Usage:
  py atomic_summer_posts.py               Preview all 67 captions
  py atomic_summer_posts.py --post N      Post caption #N to Facebook NOW
  py atomic_summer_posts.py --schedule    Schedule all 67 FB + IG posts
  py atomic_summer_posts.py --schedule-ig Schedule IG only (FB already scheduled)
  py atomic_summer_posts.py --ig N        Print caption #N for Instagram copy-paste
  py atomic_summer_posts.py --export-ig   Export all 67 IG captions to .txt file
""")

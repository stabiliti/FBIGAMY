"""
youtube_uploader.py
-------------------
Uploads a video to Amy's YouTube channel.
Works locally OR inside GitHub Actions (using Secrets for auth).

Supports resumable upload for large files (48-min Dr. Shad interview, etc.)

GitHub Secrets required (after running youtube_auth.py):
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN

Usage:
  py youtube_uploader.py "path/to/video.mp4" --title "Video Title" --description "..." --tags "tag1,tag2"
  py youtube_uploader.py "Dr Shad Interview.mp4" --title "Dr Shad Helmstetter Interview | Self-Talk" --unlisted
  py youtube_uploader.py "Export.mp4" --title "How I Got My Life Back | Amy Light" --public

Options:
  --title         Video title (required)
  --description   Video description
  --tags          Comma-separated tags
  --unlisted      Upload as unlisted (default)
  --public        Upload as public
  --private       Upload as private
  --playlist-id   Add to a playlist after upload
"""
import os, sys, json, time, math, urllib.request, urllib.parse, urllib.error, argparse

# ── CONFIG ────────────────────────────────────────────────────────────────────
CLIENT_ID      = os.environ.get("YOUTUBE_CLIENT_ID")
CLIENT_SECRET  = os.environ.get("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN  = os.environ.get("YOUTUBE_REFRESH_TOKEN")

# Fallback: read from local token file (for local use)
if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    token_file = "youtube_token.json"
    if os.path.exists(token_file):
        with open(token_file) as f:
            tok = json.load(f)
        CLIENT_ID     = CLIENT_ID     or tok.get("client_id")
        CLIENT_SECRET = CLIENT_SECRET or tok.get("client_secret")
        REFRESH_TOKEN = REFRESH_TOKEN or tok.get("refresh_token")

if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    print("ERROR: YouTube credentials not found.")
    print("Run youtube_auth.py first, then add YOUTUBE_CLIENT_ID, "
          "YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN to GitHub Secrets.")
    sys.exit(1)

CHUNK_SIZE    = 10 * 1024 * 1024  # 10MB chunks for resumable upload
TOKEN_URL     = "https://oauth2.googleapis.com/token"
UPLOAD_URL    = "https://www.googleapis.com/upload/youtube/v3/videos"
VIDEOS_URL    = "https://www.googleapis.com/youtube/v3/videos"
PLAYLIST_URL  = "https://www.googleapis.com/youtube/v3/playlistItems"

# Default channel description template
DEFAULT_DESCRIPTION = """Amy Light | Fit for Excellence

Coach. Certified Personal Trainer. Self-Talk Expert.

🌟 Ready to transform your body AND your mindset?
👉 Join the Atomic Summer Challenge: www.amylight.info/fitplustraining
📖 Get the free ALIGN Guide: mailchi.mp/10f79b32a6a0/align
🌿 Free Fiber Guide (natural GLP-1): mailchi.mp/3f4abcecea44/fiber

📱 Instagram: @coachamylight
📘 Facebook: Fit For Excellence

#fitforexcellence #amylight #coachamylight #selftalk #mindset #weightloss #healthylifestyle #atomicsummer"""

# ── AUTH ──────────────────────────────────────────────────────────────────────
def get_access_token():
    """Exchange refresh token for a fresh access token."""
    data = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

# ── RESUMABLE UPLOAD ──────────────────────────────────────────────────────────
def start_resumable_session(access_token, file_size, metadata):
    """Initialize a resumable upload session and return the upload URI."""
    meta_json = json.dumps(metadata).encode()
    params = urllib.parse.urlencode({
        "uploadType": "resumable",
        "part":       "snippet,status",
    })
    req = urllib.request.Request(
        f"{UPLOAD_URL}?{params}",
        data=meta_json,
        method="POST"
    )
    req.add_header("Authorization",     f"Bearer {access_token}")
    req.add_header("Content-Type",      "application/json; charset=UTF-8")
    req.add_header("X-Upload-Content-Type", "video/*")
    req.add_header("X-Upload-Content-Length", str(file_size))

    with urllib.request.urlopen(req, timeout=30) as r:
        return r.headers["Location"]

def upload_chunks(upload_uri, file_path, file_size):
    """Upload file in chunks, showing progress. Returns video ID on success."""
    total_chunks = math.ceil(file_size / CHUNK_SIZE)
    start = 0

    with open(file_path, "rb") as f:
        for chunk_num in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            end   = start + len(chunk) - 1

            req = urllib.request.Request(upload_uri, data=chunk, method="PUT")
            req.add_header("Content-Length", str(len(chunk)))
            req.add_header("Content-Range",  f"bytes {start}-{end}/{file_size}")
            req.add_header("Content-Type",   "video/*")

            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    body = json.loads(r.read())
                    pct  = (end + 1) / file_size * 100
                    print(f"  ✓ Upload complete! Video ID: {body.get('id')}")
                    return body.get("id")
            except urllib.error.HTTPError as e:
                if e.code == 308:  # Resume Incomplete — expected for non-final chunks
                    pct = (end + 1) / file_size * 100
                    print(f"  … chunk {chunk_num+1}/{total_chunks} ({pct:.1f}%)")
                    start = end + 1
                else:
                    body = e.read()
                    print(f"  ✗ Chunk {chunk_num+1} failed (HTTP {e.code}): {body[:200]}")
                    return None
    return None

def wait_for_processing(video_id, access_token, max_wait=300):
    """Poll until the video is done processing."""
    print(f"  Waiting for YouTube to process the video…")
    deadline = time.time() + max_wait
    while time.time() < deadline:
        params = urllib.parse.urlencode({
            "part": "status,snippet",
            "id":   video_id,
        })
        req = urllib.request.Request(f"{VIDEOS_URL}?{params}")
        req.add_header("Authorization", f"Bearer {access_token}")
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())

        items = data.get("items", [])
        if not items:
            break
        status = items[0].get("status", {})
        upload_status = status.get("uploadStatus", "")
        print(f"  … upload status: {upload_status}")

        if upload_status == "processed":
            return True
        if upload_status in ("failed", "rejected", "deleted"):
            print(f"  ✗ Processing failed: {status}")
            return False
        time.sleep(15)
    print(f"  ⚠ Timed out — video may still be processing on YouTube's end")
    return True  # Don't fail just because processing is slow

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Upload a video to Amy's YouTube channel")
    parser.add_argument("video_path",   help="Path to the video file")
    parser.add_argument("--title",      required=True, help="Video title")
    parser.add_argument("--description",default=DEFAULT_DESCRIPTION, help="Video description")
    parser.add_argument("--tags",       default="fitforexcellence,amylight,coachamylight,selftalk,mindset,weightloss,atomicsummer", help="Comma-separated tags")
    parser.add_argument("--unlisted",   action="store_true", default=True, help="Upload as unlisted (default)")
    parser.add_argument("--public",     action="store_true", help="Upload as public")
    parser.add_argument("--private",    action="store_true", help="Upload as private")
    parser.add_argument("--category",   default="26", help="YouTube category ID (26=Howto&Style, 22=People&Blogs)")
    parser.add_argument("--playlist-id",default=None, help="YouTube playlist ID to add video to")
    args = parser.parse_args()

    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        sys.exit(1)

    file_size = os.path.getsize(video_path)
    size_mb   = file_size / (1024 * 1024)

    # Determine privacy
    if args.public:
        privacy = "public"
    elif args.private:
        privacy = "private"
    else:
        privacy = "unlisted"

    print(f"YouTube Uploader — Amy Light | Fit for Excellence")
    print(f"{'='*55}")
    print(f"File:    {video_path}")
    print(f"Size:    {size_mb:.1f} MB")
    print(f"Title:   {args.title}")
    print(f"Privacy: {privacy}")
    print()

    # Get access token
    print("Authenticating with YouTube…")
    access_token = get_access_token()
    print("✓ Authenticated\n")

    # Build metadata
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    metadata = {
        "snippet": {
            "title":       args.title,
            "description": args.description,
            "tags":        tags,
            "categoryId":  args.category,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus":           privacy,
            "selfDeclaredMadeForKids": False,
        }
    }

    # Start upload session
    print("Starting resumable upload session…")
    upload_uri = start_resumable_session(access_token, file_size, metadata)
    print(f"✓ Upload session started\n")

    # Upload
    print(f"Uploading {size_mb:.1f} MB in {math.ceil(file_size / CHUNK_SIZE)} chunks…")
    video_id = upload_chunks(upload_uri, video_path, file_size)

    if not video_id:
        print("\n✗ Upload failed.")
        sys.exit(1)

    # Wait for processing
    wait_for_processing(video_id, access_token)

    # Build URLs
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    embed_url = f"https://www.youtube.com/embed/{video_id}"

    print(f"""
✓ Upload complete!

  Video ID:   {video_id}
  Watch URL:  {watch_url}
  Embed URL:  {embed_url}
  Privacy:    {privacy}

Add the Watch URL to reels_schedule.json as the video_url for IG Reels.
(Note: YouTube watch URLs don't work as IG Reel video_url — use the raw video
file via GitHub instead. YouTube is for the channel, not IG hosting.)
""")

    # Add to playlist if specified
    if args.playlist_id:
        print(f"Adding to playlist {args.playlist_id}…")
        pl_data = json.dumps({
            "snippet": {
                "playlistId": args.playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id}
            }
        }).encode()
        req = urllib.request.Request(
            f"{PLAYLIST_URL}?part=snippet",
            data=pl_data, method="POST"
        )
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Content-Type",  "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                print(f"  ✓ Added to playlist")
        except Exception as e:
            print(f"  ⚠ Could not add to playlist: {e}")

    # Save result for reference
    result = {
        "video_id":   video_id,
        "title":      args.title,
        "privacy":    privacy,
        "watch_url":  watch_url,
        "embed_url":  embed_url,
        "file":       video_path,
        "size_mb":    round(size_mb, 1),
    }
    results_file = "youtube_uploads.json"
    existing = json.load(open(results_file)) if os.path.exists(results_file) else []
    existing.append(result)
    json.dump(existing, open(results_file, "w"), indent=2)
    print(f"✓ Saved to {results_file}")

if __name__ == "__main__":
    main()

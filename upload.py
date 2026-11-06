"""
Plain Science - upload a rendered Short to YouTube via the Data API v3.

Usage:
    python upload.py D:\\Plainscience\\queue\\2026-11-06

Reads YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN from .env next to
this file (never printed), finds the .mp4 and script.md in the given queue
folder, pulls title/description/tags from script.md's "## Package" section,
uploads with videos.insert (resumable), and appends a line to log.md.

Uploads from an unaudited API project are forced to PRIVATE by YouTube
regardless of the privacyStatus requested here - that's expected until the
audit (https://support.google.com/youtube/contact/yt_api_form) is approved.
"""
import argparse
import glob
import os
import re
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
LOG_FILE = os.path.join(ROOT, "log.md")
CATEGORY_SCIENCE_TECH = "28"


def get_credentials():
    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        sys.exit("Missing YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN. "
                  "Run get_refresh_token.py first.")
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def parse_package(script_text):
    """Pull title/description/tags/topic/hook/hook-score out of script.md."""
    def field(label):
        m = re.search(rf"^{label}:\s*(.+)$", script_text, re.MULTILINE)
        return m.group(1).strip() if m else None

    title = field("Title")
    if title:
        # strip a trailing "(NN chars, ...)" note if present
        title = re.sub(r"\s*\(\d+\s*chars.*\)\s*$", "", title).strip()

    description = field("Description")
    topic = field("Topic")

    hook_m = re.search(r'^Hook \(final\):\s*"(.+?)"\s*->\s*hookscore\s*(\d+)', script_text, re.MULTILINE)
    hook = hook_m.group(1) if hook_m else None
    hook_score = hook_m.group(2) if hook_m else None

    hashtags = re.findall(r"#(\w+)", script_text)
    sources_m = re.search(r"^Sources:\s*(.+)$", script_text, re.MULTILINE)
    sources = sources_m.group(1).strip() if sources_m else ""

    desc_parts = [p for p in [description, sources] if p]
    full_description = "\n\n".join(desc_parts)

    return {
        "title": title or "Plain Science Short",
        "description": full_description,
        "tags": list(dict.fromkeys(hashtags + ["PlainScience", "Shorts"])),
        "topic": topic,
        "hook": hook,
        "hook_score": hook_score,
    }


def find_files(queue_dir):
    mp4s = glob.glob(os.path.join(queue_dir, "*.mp4"))
    if not mp4s:
        sys.exit(f"No .mp4 found in {queue_dir}")
    script_path = os.path.join(queue_dir, "script.md")
    if not os.path.exists(script_path):
        sys.exit(f"No script.md found in {queue_dir}")
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()
    return mp4s[0], script_text


def upload(youtube, video_path, package):
    body = {
        "snippet": {
            "title": package["title"][:100],
            "description": package["description"][:5000],
            "tags": package["tags"],
            "categoryId": CATEGORY_SCIENCE_TECH,
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")
    return response


def append_log(package, status_line):
    date = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    entry = (
        f"\n## {date}\n"
        f"- Topic: {package['topic'] or '(unknown)'}\n"
        f"- Final hook: \"{package['hook'] or '(unknown)'}\"\n"
        f"- Hook score: {package['hook_score'] or '(unknown)'}\n"
        f"- Title: {package['title']}\n"
        f"- Upload status: {status_line}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("queue_dir", help="Folder containing the .mp4 and script.md, e.g. D:\\Plainscience\\queue\\2026-11-06")
    args = parser.parse_args()

    video_path, script_text = find_files(args.queue_dir)
    package = parse_package(script_text)

    print(f"Title: {package['title']}")
    print(f"Video: {video_path}")

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    try:
        response = upload(youtube, video_path, package)
    except HttpError as e:
        append_log(package, f"FAILED - {e}")
        raise

    video_id = response["id"]
    url = f"https://youtu.be/{video_id}"
    privacy = response.get("status", {}).get("privacyStatus", "unknown")
    status_line = f"Uploaded PRIVATE ({privacy}) - {url} - make public in Studio after review"
    append_log(package, status_line)

    print(f"Uploaded: {url}")
    print(f"Privacy status: {privacy}")
    if privacy == "private":
        print("This project is unaudited, so YouTube forced it private. "
              "Review it in Studio and make it public yourself, then file "
              "the audit request so future uploads can go public directly.")


if __name__ == "__main__":
    main()

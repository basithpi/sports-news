from __future__ import annotations

import argparse
import asyncio
import hashlib
import html
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    import edge_tts
except ImportError:  # pragma: no cover - handled by dependency check
    edge_tts = None

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

try:
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build as build_google_service
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:  # pragma: no cover - handled by dependency check
    GoogleAuthRequest = None
    Credentials = None
    InstalledAppFlow = None
    build_google_service = None
    HttpError = Exception
    MediaFileUpload = None


WIDTH = 1080
HEIGHT = 1920
MIN_DURATION = 60
MAX_DURATION = 120
MIN_VISUAL_ASSETS = 7
TARGET_SCENE_COUNT = 8
YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
DEFAULT_STATE = {"topics": {}, "source_urls": {}, "video_hashes": {}, "uploads": []}

RSS_FEEDS = [
    {
        "name": "BBC Sport Football",
        "sport": "football",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    },
    {
        "name": "BBC Sport Cricket",
        "sport": "cricket",
        "url": "https://feeds.bbci.co.uk/sport/cricket/rss.xml",
    },
    {
        "name": "ESPN Football",
        "sport": "football",
        "url": "https://www.espn.com/espn/rss/soccer/news",
    },
    {
        "name": "ESPN Cricinfo",
        "sport": "cricket",
        "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    },
    {
        "name": "Sky Sports Football",
        "sport": "football",
        "url": "https://www.skysports.com/rss/12040",
    },
    {
        "name": "Sky Sports Cricket",
        "sport": "cricket",
        "url": "https://www.skysports.com/rss/12079",
    },
]

FOOTBALL_SCOREBOARD_LEAGUES = [
    ("Premier League", "eng.1"),
    ("UEFA Champions League", "uefa.champions"),
    ("La Liga", "esp.1"),
    ("Serie A", "ita.1"),
    ("Bundesliga", "ger.1"),
    ("Ligue 1", "fra.1"),
    ("MLS", "usa.1"),
]

TREND_KEYWORDS = [
    "goal",
    "winner",
    "wins",
    "beat",
    "beats",
    "final",
    "score",
    "record",
    "century",
    "hat-trick",
    "transfer",
    "sign",
    "premier league",
    "champions league",
    "fifa",
    "icc",
    "ipl",
    "world cup",
    "breaking",
    "stuns",
    "thriller",
    "comeback",
    "milestone",
]

IMPORTANT_WORDS = [
    "GOAL",
    "WINNER",
    "CENTURY",
    "HAT-TRICK",
    "RECORD",
    "FINAL SCORE",
    "BREAKING",
    "TRANSFER",
    "IPL",
    "ICC",
]

PALETTES = [
    ("#101820", "#FEE715", "#16A085", "#F4F7FA"),
    ("#0B132B", "#F45B69", "#3A86FF", "#F8F9FA"),
    ("#111827", "#22C55E", "#F97316", "#F9FAFB"),
    ("#151515", "#00D1B2", "#FFDD57", "#F5F5F5"),
    ("#17202A", "#E74C3C", "#2ECC71", "#ECF0F1"),
]


@dataclass
class NewsItem:
    title: str
    summary: str
    link: str
    source: str
    sport: str
    published: str | None
    published_ts: float
    score: float
    image_url: str | None = None


@dataclass
class ImageAsset:
    path: str
    source: str
    source_url: str
    credit: str
    license: str


@dataclass
class ShortPackage:
    video_title: str
    news_source: str
    source_url: str
    script: str
    voiceover_text: str
    scene_breakdown: list[dict[str, str]]
    image_prompts: list[dict[str, str]]
    caption_file: str
    thumbnail_text: str
    description: str
    hashtags: list[str]
    video_file: str
    visual_assets: list[ImageAsset]


@dataclass
class YouTubeUpload:
    video_id: str
    video_url: str
    title: str
    local_file: str
    scheduled_publish_at: str
    privacy_status: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate automated football and cricket YouTube Shorts.")
    parser.add_argument("--count", type=int, default=int(os.getenv("SHORTS_PER_RUN", "10")))
    parser.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "output"))
    parser.add_argument("--voice", default=os.getenv("EDGE_TTS_VOICE", "en-US-GuyNeural"))
    parser.add_argument("--dry-run", action="store_true", help="Generate scripts and metadata without audio/video rendering.")
    parser.add_argument("--upload-youtube", action="store_true", help="Upload generated Shorts to YouTube and schedule them.")
    parser.add_argument("--youtube-client-secrets", default=os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secret.json"))
    parser.add_argument("--youtube-token-file", default=os.getenv("YOUTUBE_TOKEN_FILE", "token.json"))
    parser.add_argument("--schedule-start", default=os.getenv("YOUTUBE_SCHEDULE_START", ""), help="Optional ISO datetime for the first scheduled publish time.")
    parser.add_argument("--schedule-delay-minutes", type=int, default=int(os.getenv("YOUTUBE_SCHEDULE_DELAY_MINUTES", "20")))
    parser.add_argument("--schedule-interval-minutes", type=int, default=int(os.getenv("YOUTUBE_SCHEDULE_INTERVAL_MINUTES", "20")))
    parser.add_argument("--youtube-category-id", default=os.getenv("YOUTUBE_CATEGORY_ID", "17"), help="YouTube category id. 17 is Sports.")
    parser.add_argument("--made-for-kids", action="store_true", help="Mark uploaded videos as made for kids.")
    parser.add_argument("--state-file", default=os.getenv("PIPELINE_STATE_FILE", ".sports_shorts_state.json"))
    parser.add_argument("--keep-old-runs", action="store_true", help="Keep older output folders instead of deleting them after this run.")
    parser.add_argument("--no-upload-youtube", action="store_true", help="Generate only. Overrides the default auto-upload behavior.")
    parser.add_argument("--daily-loop", action="store_true", help="Keep running and start one pipeline run per day at --daily-time.")
    parser.add_argument("--daily-time", default=os.getenv("DAILY_UPLOAD_TIME", "08:00"), help="Local machine time for --daily-loop, in HH:MM 24-hour format.")
    parser.add_argument(
        "--dedupe-scope",
        choices=["same-day", "forever"],
        default=os.getenv("DEDUPE_SCOPE", "same-day"),
        help="Duplicate protection window. same-day blocks repeats only for the current local date; forever keeps the historical behavior.",
    )
    args = parser.parse_args()
    if not args.no_upload_youtube:
        args.upload_youtube = True

    validate_daily_time(args.daily_time)
    require_tools(render=not args.dry_run, upload_youtube=args.upload_youtube)
    if args.upload_youtube and args.dry_run:
        raise SystemExit("--upload-youtube cannot be used with --dry-run because there is no MP4 to upload.")
    if args.upload_youtube and not Path(args.youtube_client_secrets).exists():
        raise SystemExit(
            f"YouTube OAuth client file not found: {Path(args.youtube_client_secrets).resolve()}\n"
            "Create an OAuth Desktop client in Google Cloud, download it, and save it at this path."
        )

    if args.daily_loop:
        run_daily_loop(args)
        return

    run_once(args)


def run_daily_loop(args: argparse.Namespace) -> None:
    print(f"Daily loop enabled. Next runs start at {args.daily_time} local time.")
    while True:
        run_at = next_daily_run_time(args.daily_time)
        sleep_seconds = max(0.0, (run_at - datetime.now().astimezone()).total_seconds())
        print(f"Next daily run: {run_at.isoformat()}")
        time.sleep(sleep_seconds)
        try:
            run_once(args)
        except Exception as exc:
            print(f"Daily run failed: {exc}")
        time.sleep(60)


def run_once(args: argparse.Namespace) -> None:
    run_dir = Path(args.output_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = Path(args.state_file)
    state = load_pipeline_state(state_path)

    print("Fetching current football and cricket stories...")
    items = fetch_sports_news()
    selected = select_topics(items, args.count, state=state, dedupe_scope=args.dedupe_scope)
    if len(selected) < args.count:
        print(f"Only found {len(selected)} unique current topics from free feeds.")

    packages: list[ShortPackage] = []
    uploads: list[YouTubeUpload] = []
    videos_dir = run_dir / "videos"
    videos_dir.mkdir(exist_ok=True)
    youtube = None
    fixed_first_publish_at = None
    last_publish_at = None
    if args.upload_youtube:
        print("YouTube upload is enabled. Each Short will upload immediately after it is created.")
        youtube = build_youtube_client(Path(args.youtube_client_secrets), Path(args.youtube_token_file))
        fixed_first_publish_at = parse_schedule_start(args.schedule_start, args.schedule_delay_minutes) if args.schedule_start else None

    for index, item in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] Building Short: {item.title}")
        package_dir = unique_dir(run_dir, slugify(item.title)[:58])
        package_dir.mkdir(parents=True, exist_ok=True)
        package = build_short(item, package_dir, args.voice, dry_run=args.dry_run)
        if package.video_file:
            flat_video = unique_file(videos_dir, Path(package.video_file).name)
            shutil.copy2(package.video_file, flat_video)
        packages.append(package)

        if args.upload_youtube:
            uploadable = filter_previously_uploaded_packages([package], state, args.dedupe_scope)
            if not uploadable:
                continue
            if fixed_first_publish_at:
                publish_at = fixed_first_publish_at + timedelta(minutes=args.schedule_interval_minutes * len(uploads))
            else:
                publish_at = next_publish_time_after_upload(
                    last_publish_at=last_publish_at,
                    delay_minutes=args.schedule_delay_minutes,
                    interval_minutes=args.schedule_interval_minutes,
                )
            print(f"Uploading now: {Path(package.video_file).name}")
            print(f"Scheduled public time: {publish_at.astimezone(timezone.utc).isoformat()}")
            upload = upload_one_youtube_short(
                youtube=youtube,
                package=package,
                publish_at=publish_at,
                category_id=args.youtube_category_id,
                made_for_kids=args.made_for_kids,
            )
            uploads.append(upload)
            last_publish_at = publish_at
            record_successful_run(state, [package], [upload], args.dedupe_scope)
            save_pipeline_state(state_path, state)
            delete_uploaded_local_videos(package, videos_dir)
            print(f"Uploaded: {upload.video_url}")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(packages),
        "packages": [asdict(package) for package in packages],
    }

    if args.upload_youtube:
        manifest["youtube_uploads"] = [asdict(upload) for upload in uploads]
        (run_dir / "youtube_uploads.json").write_text(
            json.dumps([asdict(upload) for upload in uploads], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    else:
        record_generated_topics(state, packages, args.dedupe_scope)
        save_pipeline_state(state_path, state)

    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    delete_old_output_runs(Path(args.output_dir), keep=run_dir, enabled=not args.keep_old_runs)
    print(f"Done. Output saved to: {run_dir.resolve()}")


def require_tools(render: bool, upload_youtube: bool = False) -> None:
    if render and shutil.which("ffmpeg") is None:
        raise SystemExit("FFmpeg is required on PATH.")
    if render and edge_tts is None:
        raise SystemExit("edge-tts is missing. Run: pip install -r requirements.txt")
    if upload_youtube and not all([GoogleAuthRequest, Credentials, InstalledAppFlow, build_google_service, MediaFileUpload]):
        raise SystemExit("YouTube upload dependencies are missing. Run: pip install -r requirements.txt")


def validate_daily_time(time_str: str) -> None:
    """Validate that time_str is in HH:MM 24-hour format."""
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid format")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError("Invalid time values")
    except (ValueError, AttributeError):
        raise SystemExit(f"--daily-time must be in HH:MM 24-hour format (e.g., 08:00), got: {time_str}")


def next_daily_run_time(time_str: str) -> datetime:
    """Calculate next run time for daily loop based on HH:MM time string."""
    now = datetime.now()
    hour, minute = map(int, time_str.split(":"))
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run


def load_pipeline_state(path: Path) -> dict:
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_STATE))
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return json.loads(json.dumps(DEFAULT_STATE))
    for key, default_value in DEFAULT_STATE.items():
        state.setdefault(key, default_value.copy() if isinstance(default_value, dict) else list(default_value))
    return state


def save_pipeline_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def topic_state_key(title: str) -> str:
    normalized = normalize_key(title)
    tokens = [token for token in normalized.split() if len(token) > 2]
    return " ".join(tokens[:14])


def package_topic_key(package: ShortPackage) -> str:
    return topic_state_key(package.video_title)


def state_has_topic(state: dict, item: NewsItem) -> bool:
    if item.link and item.link in state.get("source_urls", {}):
        return True
    key = topic_state_key(item.title)
    return key in state.get("topics", {})


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filter_previously_uploaded_packages(packages: list[ShortPackage], state: dict, dedupe_scope: str = "same-day") -> list[ShortPackage]:
    filtered: list[ShortPackage] = []
    for package in packages:
        video_path = Path(package.video_file)
        if not video_path.exists():
            continue
        topic_key = package_topic_key(package)
        video_hash = file_sha256(video_path)
        if topic_key in state.get("topics", {}) or package.source_url in state.get("source_urls", {}) or video_hash in state.get("video_hashes", {}):
            print(f"Skipping duplicate upload: {package.video_title}")
            continue
        filtered.append(package)
    return filtered


def record_generated_topics(state: dict, packages: list[ShortPackage], dedupe_scope: str = "same-day") -> None:
    now = datetime.now(timezone.utc).isoformat()
    for package in packages:
        key = package_topic_key(package)
        state.setdefault("topics", {})[key] = {"title": package.video_title, "seen_at": now, "source_url": package.source_url}
        if package.source_url:
            state.setdefault("source_urls", {})[package.source_url] = {"title": package.video_title, "seen_at": now}


def record_successful_run(state: dict, packages: list[ShortPackage], uploads: list[YouTubeUpload], dedupe_scope: str = "same-day") -> None:
    now = datetime.now(timezone.utc).isoformat()
    upload_by_file = {Path(upload.local_file).resolve(): upload for upload in uploads}
    for package in packages:
        video_path = Path(package.video_file)
        resolved = video_path.resolve()
        upload = upload_by_file.get(resolved)
        if not upload:
            continue
        key = package_topic_key(package)
        video_hash = file_sha256(video_path)
        state.setdefault("topics", {})[key] = {
            "title": package.video_title,
            "uploaded_at": now,
            "source_url": package.source_url,
            "youtube_video_id": upload.video_id,
        }
        if package.source_url:
            state.setdefault("source_urls", {})[package.source_url] = {"title": package.video_title, "uploaded_at": now}
        state.setdefault("video_hashes", {})[video_hash] = {"title": package.video_title, "uploaded_at": now, "youtube_video_id": upload.video_id}
        state.setdefault("uploads", []).append(asdict(upload))


def delete_old_output_runs(output_dir: Path, keep: Path, enabled: bool) -> None:
    if not enabled or not output_dir.exists():
        return
    keep = keep.resolve()
    for child in output_dir.iterdir():
        if not child.is_dir():
            continue
        if child.resolve() == keep:
            continue
        if not re.fullmatch(r"\d{8}_\d{6}", child.name):
            continue
        shutil.rmtree(child, ignore_errors=True)


def delete_uploaded_local_videos(package: ShortPackage, videos_dir: Path) -> None:
    video_path = Path(package.video_file)
    candidates = [
        video_path,
        video_path.parent / "silent.mp4",
        videos_dir / video_path.name,
    ]
    for candidate in candidates:
        try:
            candidate.unlink(missing_ok=True)
        except OSError as exc:
            print(f"Warning: could not delete local uploaded video {candidate}: {exc}")


def next_publish_time_after_upload(last_publish_at: datetime | None, delay_minutes: int, interval_minutes: int) -> datetime:
    earliest = datetime.now().astimezone() + timedelta(minutes=max(1, delay_minutes))
    if not last_publish_at:
        return earliest
    spaced = last_publish_at + timedelta(minutes=max(1, interval_minutes))
    return max(earliest, spaced)


def upload_youtube_packages(packages: list[ShortPackage], args: argparse.Namespace) -> list[YouTubeUpload]:
    client_secrets = Path(args.youtube_client_secrets)
    if not client_secrets.exists():
        raise SystemExit(
            f"YouTube OAuth client file not found: {client_secrets.resolve()}\n"
            "Create an OAuth Desktop client in Google Cloud, download it, and save it at this path."
        )

    youtube = build_youtube_client(client_secrets, Path(args.youtube_token_file))
    first_publish_at = parse_schedule_start(args.schedule_start, args.schedule_delay_minutes) if args.schedule_start else None
    uploads: list[YouTubeUpload] = []

    uploadable = [package for package in packages if package.video_file and Path(package.video_file).exists()]
    for index, package in enumerate(uploadable):
        if first_publish_at:
            publish_at = first_publish_at + timedelta(minutes=args.schedule_interval_minutes * index)
        else:
            publish_at = datetime.now().astimezone() + timedelta(minutes=max(1, args.schedule_delay_minutes))
        print(f"Uploading {Path(package.video_file).name} -> scheduled {publish_at.astimezone(timezone.utc).isoformat()}")
        upload = upload_one_youtube_short(
            youtube=youtube,
            package=package,
            publish_at=publish_at,
            category_id=args.youtube_category_id,
            made_for_kids=args.made_for_kids,
        )
        uploads.append(upload)
        print(f"Uploaded: {upload.video_url}")

    return uploads


def build_youtube_client(client_secrets: Path, token_file: Path):
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), YOUTUBE_UPLOAD_SCOPE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), YOUTUBE_UPLOAD_SCOPE)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json(), encoding="utf-8")
    return build_google_service("youtube", "v3", credentials=creds)


def upload_one_youtube_short(
    youtube,
    package: ShortPackage,
    publish_at: datetime,
    category_id: str,
    made_for_kids: bool,
) -> YouTubeUpload:
    utc_publish_at = publish_at.astimezone(timezone.utc)
    title = short_line(package.video_title, 95)
    description = build_youtube_description(package)
    tags = build_youtube_tags(package)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": youtube_rfc3339(utc_publish_at),
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    media = MediaFileUpload(package.video_file, chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=False,
    )
    response = resumable_upload(request)
    video_id = response["id"]
    return YouTubeUpload(
        video_id=video_id,
        video_url=f"https://www.youtube.com/watch?v={video_id}",
        title=title,
        local_file=package.video_file,
        scheduled_publish_at=youtube_rfc3339(utc_publish_at),
        privacy_status="private",
    )


def resumable_upload(request, max_retries: int = 5) -> dict:
    retry = 0
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        except HttpError as exc:
            if getattr(exc, "resp", None) and exc.resp.status in {500, 502, 503, 504} and retry < max_retries:
                sleep_seconds = 2 ** retry
                print(f"YouTube upload retry in {sleep_seconds}s after HTTP {exc.resp.status}.")
                time.sleep(sleep_seconds)
                retry += 1
                continue
            raise
        except Exception:
            if retry >= max_retries:
                raise
            sleep_seconds = 2 ** retry
            print(f"YouTube upload retry in {sleep_seconds}s after a transient error.")
            time.sleep(sleep_seconds)
            retry += 1
    return response


def parse_schedule_start(value: str, delay_minutes: int) -> datetime:
    if value:
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise SystemExit("--schedule-start must be an ISO datetime, for example 2026-06-01T10:00:00+05:30") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return ensure_future_schedule(parsed)
    return datetime.now().astimezone() + timedelta(minutes=max(1, delay_minutes))


def ensure_future_schedule(value: datetime) -> datetime:
    minimum = datetime.now(timezone.utc) + timedelta(minutes=2)
    if value.astimezone(timezone.utc) < minimum:
        raise SystemExit("The YouTube schedule time must be in the future. Use --schedule-start or increase --schedule-delay-minutes.")
    return value


def youtube_rfc3339(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_youtube_description(package: ShortPackage) -> str:
    hashtags = package.hashtags[:]
    if "#Shorts" not in hashtags:
        hashtags.append("#Shorts")
    text = f"{package.description}\n\n{' '.join(hashtags)}"
    return text[:5000]


def build_youtube_tags(package: ShortPackage) -> list[str]:
    tags = [tag.lstrip("#") for tag in package.hashtags]
    tags.extend(["Shorts", "Sports News", "Football", "Cricket"])
    deduped: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = short_line(re.sub(r"\s+", " ", tag).strip(), 30)
        key = cleaned.lower()
        if cleaned and key not in seen:
            deduped.append(cleaned)
            seen.add(key)
    return deduped[:25]


def fetch_sports_news() -> list[NewsItem]:
    items: list[NewsItem] = []
    for feed in RSS_FEEDS:
        try:
            response = requests.get(feed["url"], timeout=20, headers={"User-Agent": "SportsShortsBot/1.0"})
            response.raise_for_status()
            items.extend(parse_rss(response.text, feed["name"], feed["sport"]))
        except Exception as exc:
            print(f"Warning: could not fetch {feed['name']}: {exc}")
    items.extend(fetch_football_scoreboard_items())
    deduped: dict[str, NewsItem] = {}
    for item in items:
        key = normalize_key(item.title)
        if key not in deduped or item.score > deduped[key].score:
            deduped[key] = item
    return sorted(deduped.values(), key=lambda x: x.score, reverse=True)


def fetch_football_scoreboard_items() -> list[NewsItem]:
    items: list[NewsItem] = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    dates = [
        (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y%m%d"),
        today,
        (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y%m%d"),
    ]
    for league_name, league_code in FOOTBALL_SCOREBOARD_LEAGUES:
        for date_value in dates:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard?dates={date_value}"
            try:
                response = requests.get(url, timeout=20, headers={"User-Agent": "SportsShortsBot/1.0"})
                response.raise_for_status()
                items.extend(parse_espn_scoreboard(response.json(), league_name, url))
            except Exception as exc:
                print(f"Warning: could not fetch ESPN {league_name} scoreboard: {exc}")
    return items


def parse_espn_scoreboard(payload: dict, league_name: str, source_url: str) -> list[NewsItem]:
    parsed: list[NewsItem] = []
    for event in payload.get("events", []):
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []
        if len(competitors) < 2:
            continue
        home = next((team for team in competitors if team.get("homeAway") == "home"), competitors[0])
        away = next((team for team in competitors if team.get("homeAway") == "away"), competitors[1])
        home_name = home.get("team", {}).get("displayName") or home.get("team", {}).get("name", "Home")
        away_name = away.get("team", {}).get("displayName") or away.get("team", {}).get("name", "Away")
        home_score = home.get("score")
        away_score = away.get("score")
        status = competition.get("status", {}).get("type", {})
        status_text = status.get("description") or status.get("shortDetail") or "Scheduled"
        event_date = event.get("date", "")
        published_ts = parse_iso_ts(event_date)
        is_final = bool(status.get("completed"))
        is_live = str(status.get("state", "")).lower() == "in"
        if is_final and home_score is not None and away_score is not None:
            title = f"{home_name} {home_score}-{away_score} {away_name}: {league_name} result"
            summary = f"Final score from {league_name}: {home_name} {home_score}, {away_name} {away_score}. Key result and fixture impact for football fans."
        elif is_live:
            score_text = f"{home_score}-{away_score}" if home_score is not None and away_score is not None else "live"
            title = f"Live football update: {home_name} vs {away_name} is {score_text}"
            summary = f"Live {league_name} fixture update: {home_name} vs {away_name}. Current status: {status_text}. Follow the match momentum and talking points."
        else:
            title = f"Fixture highlight: {home_name} vs {away_name} in {league_name}"
            summary = f"Upcoming {league_name} fixture: {home_name} vs {away_name}. Kickoff status: {status_text}. Key fixture preview for today's football schedule."
        parsed.append(
            NewsItem(
                title=title,
                summary=summary,
                link=event.get("links", [{}])[0].get("href", source_url) if event.get("links") else source_url,
                source=f"ESPN Scoreboard - {league_name}",
                sport="football",
                published=datetime.fromtimestamp(published_ts, timezone.utc).isoformat() if published_ts else None,
                published_ts=published_ts or datetime.now(timezone.utc).timestamp(),
                score=score_item(title, summary, published_ts, "football") + (35 if is_live else 20 if is_final else 12),
                image_url=extract_competitor_logo(home) or extract_competitor_logo(away),
            )
        )
    return parsed


def extract_competitor_logo(competitor: dict) -> str | None:
    logos = competitor.get("team", {}).get("logos") or []
    if not logos:
        return None
    return logos[0].get("href")


def parse_iso_ts(value: str) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def parse_rss(xml_text: str, source: str, sport: str) -> list[NewsItem]:
    root = ElementTree.fromstring(xml_text)
    channel_items = root.findall(".//item")
    parsed: list[NewsItem] = []
    for node in channel_items:
        title = clean_text(find_text(node, "title"))
        summary = clean_text(find_text(node, "description"))
        link = clean_text(find_text(node, "link"))
        published_raw = find_text(node, "pubDate") or find_text(node, "published")
        published_ts = parse_date_ts(published_raw)
        if not title or not link:
            continue
        score = score_item(title, summary, published_ts, sport)
        parsed.append(
            NewsItem(
                title=title,
                summary=summary,
                link=link,
                source=source,
                sport=sport,
                published=datetime.fromtimestamp(published_ts, timezone.utc).isoformat() if published_ts else None,
                published_ts=published_ts,
                score=score,
                image_url=find_media_url(node),
            )
        )
    return parsed


def find_media_url(node: ElementTree.Element) -> str | None:
    for child in node.iter():
        tag = child.tag.split("}", 1)[-1].lower()
        url = child.attrib.get("url") or child.attrib.get("href")
        media_type = child.attrib.get("type", "")
        if url and tag in {"thumbnail", "content"}:
            return url
        if url and tag == "enclosure" and media_type.startswith("image/"):
            return url
    return None


def find_text(node: ElementTree.Element, tag: str) -> str:
    found = node.find(tag)
    return found.text if found is not None and found.text else ""


def parse_date_ts(value: str) -> float:
    if not value:
        return 0.0
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def score_item(title: str, summary: str, published_ts: float, sport: str) -> float:
    text = f"{title} {summary}".lower()
    score = 0.0
    now = datetime.now(timezone.utc).timestamp()
    age_hours = (now - published_ts) / 3600 if published_ts else 72
    if age_hours <= 24:
        score += 50
    elif age_hours <= 72:
        score += 25
    score += max(0, 20 - age_hours / 4)
    score += sum(8 for keyword in TREND_KEYWORDS if keyword in text)
    if sport == "football" and any(k in text for k in ["premier league", "champions league", "fifa", "transfer"]):
        score += 15
    if sport == "cricket" and any(k in text for k in ["icc", "ipl", "century", "wicket", "test", "odi", "t20"]):
        score += 15
    return score


def select_topics(items: list[NewsItem], count: int, state: dict | None = None, dedupe_scope: str = "same-day") -> list[NewsItem]:
    selected: list[NewsItem] = []
    seen_domains: dict[str, int] = {}
    seen_entities: set[str] = set()
    state = state or DEFAULT_STATE
    fresh_items = [item for item in items if not state_has_topic(state, item)]
    sports_target = {"football": math.ceil(count / 2), "cricket": count // 2}
    for sport in ["football", "cricket"]:
        for item in [x for x in fresh_items if x.sport == sport]:
            if len([x for x in selected if x.sport == sport]) >= sports_target[sport]:
                break
            if is_duplicate_topic(item, selected):
                continue
            entities = topic_entities(item.title)
            if entities & seen_entities:
                continue
            domain = urlparse(item.link).netloc
            if seen_domains.get(domain, 0) >= 4:
                continue
            selected.append(item)
            seen_entities.update(entities)
            seen_domains[domain] = seen_domains.get(domain, 0) + 1
    for item in fresh_items:
        if len(selected) >= count:
            break
        entities = topic_entities(item.title)
        if not is_duplicate_topic(item, selected) and not (entities & seen_entities):
            selected.append(item)
            seen_entities.update(entities)
    return selected[:count]


def is_duplicate_topic(item: NewsItem, selected: Iterable[NewsItem]) -> bool:
    item_words = set(normalize_key(item.title).split())
    item_entities = topic_entities(item.title)
    for existing in selected:
        existing_words = set(normalize_key(existing.title).split())
        existing_entities = topic_entities(existing.title)
        overlap = len(item_words & existing_words) / max(1, len(item_words | existing_words))
        entity_overlap = item_entities & existing_entities
        if overlap > 0.48 or len(entity_overlap) >= 2:
            return True
    return False


def topic_entities(title: str) -> set[str]:
    stopwords = {
        "after",
        "again",
        "before",
        "from",
        "have",
        "into",
        "over",
        "that",
        "their",
        "this",
        "with",
        "will",
        "your",
        "sport",
        "sports",
        "champions",
        "world",
        "cup",
        "ipl",
        "icc",
        "uefa",
        "fifa",
        "league",
        "final",
        "match",
        "news",
        "wins",
        "won",
        "beat",
        "beats",
    }
    tokens = re.findall(r"[A-Za-z0-9'-]{3,}", title)
    entities = set()
    for token in tokens:
        normalized = token.lower().strip("'")
        normalized = re.sub(r"'s$", "", normalized)
        if normalized not in stopwords and (token[:1].isupper() or token.isupper() or len(token) > 5):
            entities.add(normalized)
    return entities


def build_short(item: NewsItem, package_dir: Path, voice: str, dry_run: bool = False) -> ShortPackage:
    image_prompt_scenes = generate_structured_short_scenes(item)
    script = structured_scenes_to_script(image_prompt_scenes)
    scenes = generate_scenes(item, script)
    title = generate_video_title(item)
    description = generate_description(item)
    hashtags = generate_hashtags(item)
    thumbnail_text = generate_thumbnail_text(item)
    visual_assets = collect_visual_assets(item, package_dir / "visual_assets")

    (package_dir / "script.txt").write_text(script, encoding="utf-8")
    (package_dir / "voiceover.txt").write_text(script, encoding="utf-8")
    (package_dir / "scene_breakdown.txt").write_text(json.dumps(scenes, indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "image_prompts.json").write_text(
        json.dumps(image_prompt_scenes, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (package_dir / "image_prompts_table.md").write_text(
        build_image_prompts_table(image_prompt_scenes),
        encoding="utf-8",
    )
    (package_dir / "visual_assets.json").write_text(
        json.dumps([asdict(asset) for asset in visual_assets], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    video_path = package_dir / f"{slugify(title)[:92]}.mp4"

    if dry_run:
        pass
    else:
        audio_path = package_dir / "voiceover.mp3"
        asyncio.run(generate_voice(script, audio_path, voice))
        duration = clamp(probe_duration(audio_path), MIN_DURATION, MAX_DURATION)
        scene_paths = render_scene_images(item, scenes, package_dir, visual_assets)
        render_video(scene_paths, audio_path, video_path, duration)

    package = ShortPackage(
        video_title=title,
        news_source=item.source,
        source_url=item.link,
        script=script,
        voiceover_text=script,
        scene_breakdown=scenes,
        image_prompts=image_prompt_scenes,
        caption_file="",
        thumbnail_text=thumbnail_text,
        description=description,
        hashtags=hashtags,
        video_file=str(video_path.resolve()) if video_path.exists() else "",
        visual_assets=visual_assets,
    )
    (package_dir / "metadata.json").write_text(json.dumps(asdict(package), indent=2, ensure_ascii=False), encoding="utf-8")
    return package


STRUCTURED_GENERATION_PROMPT = """Act as an expert sports journalist and viral YouTube Shorts producer.
Return JSON only, using this exact shape:
{
  "scenes": [
    {
      "voiceover": "Fast-paced spoken narration for this scene.",
      "image_prompt": "Detailed photorealistic AI image prompt ending with --ar 9:16."
    }
  ]
}

Rules:
- Build a daily football or cricket news Short from the supplied headline, summary, source, sport, and published date.
- Keep the full voiceover under 60 seconds, with a massive hook in the first scene.
- Each image_prompt must be tailored to the specific news and must include vertical 9:16 aspect ratio or --ar 9:16.
- Do not include subtitle formatting, lower-third directions, captions, typography, graphic overlay, or on-screen wording instructions in the voiceover or image prompts.
- Use only confirmed facts from the supplied news data. If a score is unavailable, say the confirmed angle instead of inventing numbers.
"""


def build_structured_generation_prompt(item: NewsItem) -> str:
    payload = {
        "headline": item.title,
        "summary": item.summary,
        "source": item.source,
        "sport": item.sport,
        "published": item.published,
        "source_url": item.link,
    }
    return f"{STRUCTURED_GENERATION_PROMPT}\nNews data:\n{json.dumps(payload, indent=2, ensure_ascii=False)}"


def parse_structured_scene_response(response_text: str) -> list[dict[str, str]]:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Structured scene response must be valid JSON.") from exc
    scenes = payload.get("scenes") if isinstance(payload, dict) else payload
    if not isinstance(scenes, list):
        raise ValueError("Structured scene response must contain a scenes array.")
    parsed: list[dict[str, str]] = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} must be a JSON object.")
        voiceover = clean_text(str(scene.get("voiceover", ""))).strip()
        image_prompt = clean_text(str(scene.get("image_prompt", ""))).strip()
        if not voiceover or not image_prompt:
            raise ValueError(f"Scene {index} must include voiceover and image_prompt.")
        if "--ar 9:16" not in image_prompt and "vertical 9:16" not in image_prompt.lower():
            image_prompt = f"{image_prompt}, vertical 9:16 aspect ratio, --ar 9:16"
        parsed.append({"scene": str(index), "voiceover": voiceover, "image_prompt": image_prompt})
    return parsed


def generate_script(item: NewsItem) -> str:
    return structured_scenes_to_script(generate_structured_short_scenes(item))


def generate_structured_short_scenes(item: NewsItem) -> list[dict[str, str]]:
    summary = item.summary or "The latest update is developing, and fans are watching closely."
    score_line = extract_score_line(item.title, summary)
    sport_context = "football" if item.sport == "football" else "cricket"
    tournament_line = infer_tournament_line(item.title, summary, item.sport)
    stats_line = infer_stats_line(item.title, summary, item.sport)
    title = ensure_sentence(short_voice_line(item.title, 92))
    short_summary = ensure_sentence(short_voice_line(summary, 128))
    context_words = story_context_words(item)

    scene_voiceovers = [
        f"Stop scrolling. Today's biggest {sport_context} update is moving fast: {title}",
        f"Here is the quick story: {short_summary}",
        score_line,
        tournament_line,
        "The pressure point is simple: one decision, one spell, one finish, or one attacking move can flip the entire debate.",
        stats_line,
        "For fans, this matters because it can shift rankings, selection calls, momentum, and the next fixture.",
        f"Source check: this report comes from {item.source}. Follow the next update before this story changes again.",
    ]
    return [
        {
            "scene": str(index),
            "voiceover": voiceover,
            "image_prompt": build_vertical_image_prompt(item, voiceover, context_words, index),
        }
        for index, voiceover in enumerate(scene_voiceovers, start=1)
        if voiceover
    ]


def structured_scenes_to_script(scenes: list[dict[str, str]]) -> str:
    return " ".join(scene["voiceover"] for scene in scenes if scene.get("voiceover")).strip()


def build_image_prompts_table(scenes: list[dict[str, str]]) -> str:
    lines = ["| Voiceover | Vertical Image Prompt |", "|---|---|"]
    for scene in scenes:
        voiceover = markdown_table_cell(scene.get("voiceover", ""))
        image_prompt = markdown_table_cell(scene.get("image_prompt", ""))
        lines.append(f"| {voiceover} | {image_prompt} |")
    return "\n".join(lines) + "\n"


def markdown_table_cell(value: str) -> str:
    return clean_text(value).replace("|", "\\|")


def ensure_sentence(value: str) -> str:
    value = clean_text(value)
    if not value:
        return value
    return value if value[-1] in ".?!" else f"{value}."


def short_voice_line(value: str, limit: int) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    trimmed = value[:limit].rstrip()
    for separator in (". ", "; ", ": ", ", "):
        cut = trimmed.rfind(separator)
        if cut >= max(40, limit // 2):
            return trimmed[: cut + 1].strip()
    cut = trimmed.rfind(" ")
    if cut >= max(40, limit // 2):
        trimmed = trimmed[:cut].strip()
    trailing_fillers = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "through",
        "to",
        "with",
    }
    words = trimmed.split()
    while words and words[-1].lower().strip(".,;:") in trailing_fillers:
        words.pop()
    return " ".join(words).strip() or trimmed.strip()


def story_context_words(item: NewsItem) -> str:
    text = clean_text(f"{item.title}. {item.summary}")
    keywords = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", text)
    stopwords = {
        "about",
        "after",
        "against",
        "before",
        "because",
        "between",
        "from",
        "have",
        "latest",
        "match",
        "news",
        "over",
        "report",
        "said",
        "source",
        "their",
        "this",
        "with",
    }
    selected: list[str] = []
    for word in keywords:
        normalized = word.lower().strip("'")
        if normalized not in stopwords and normalized not in [item.lower() for item in selected]:
            selected.append(word)
        if len(selected) >= 8:
            break
    return ", ".join(selected) if selected else item.sport


def build_vertical_image_prompt(item: NewsItem, voiceover: str, context_words: str, index: int) -> str:
    sport_detail = (
        "elite footballers, stadium floodlights, packed stands, tactical intensity"
        if item.sport == "football"
        else "elite cricketers, floodlit pitch, tense field placements, match-day atmosphere"
    )
    scene_styles = [
        "a fan freezing mid-scroll as a huge sports moment breaks in the background",
        "athletes and coaches reacting to the central news angle with urgent body language",
        "players at the decisive phase of play, officials nearby, crowd energy rising",
        "wide international tournament atmosphere with supporters from many nations",
        "a pressure moment frozen at peak action, sweat, motion blur, and dramatic lighting",
        "close-up performance detail showing speed, timing, technique, and match pressure",
        "fans debating passionately outside a stadium after a major result or selection call",
        "sports journalists and producers verifying the story in a high-energy media workspace",
    ]
    visual = scene_styles[(index - 1) % len(scene_styles)]
    return (
        f"Photorealistic vertical 9:16 aspect ratio sports image for a mobile YouTube Short, "
        f"{visual}, inspired by this confirmed {item.sport} news: {short_line(item.title, 110)}, "
        f"key context: {context_words}, {sport_detail}, cinematic contrast, sharp focus, "
        f"natural emotion, premium editorial sports photography, ultra-detailed, --ar 9:16"
    )


def extract_score_line(title: str, summary: str) -> str:
    text = f"{title}. {summary}"
    patterns = [
        r"\b\d{1,3}-\d{1,3}\b",
        r"\b\d{2,3}/\d{1,2}\b",
        r"\b\d{2,3}\s*(?:all out|ao)\b",
        r"\bwon by [^.]+",
        r"\bbeat[s]? [^.]+",
    ]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    if matches:
        found = "; ".join(dict.fromkeys(matches[:3]))
        return f"Final score watch: {found}."
    return "No complete scoreline is confirmed in the source yet, so focus on the verified headline and key talking points."


def infer_tournament_line(title: str, summary: str, sport: str) -> str:
    text = f"{title} {summary}".lower()
    mapping = [
        ("premier league", "Premier League stakes are front and center here."),
        ("champions league", "Champions League pressure makes this one even bigger."),
        ("fifa", "FIFA competition context gives this story global reach."),
        ("ipl", "IPL impact is huge here, with points-table and fan momentum on the line."),
        ("icc", "ICC tournament context makes every moment feel amplified."),
        ("world cup", "World Cup context means the result can define a campaign."),
        ("transfer", "Transfer-market attention is the major angle, with fans tracking every twist."),
    ]
    for key, line in mapping:
        if key in text:
            return line
    if sport == "football":
        return "Football momentum can flip quickly, and this update gives fans plenty to debate."
    return "Cricket momentum can turn in a single over, and this update has that high-pressure feel."


def infer_stats_line(title: str, summary: str, sport: str) -> str:
    text = f"{title} {summary}".lower()
    if "record" in text:
        return "Interesting stat: the record angle is the main reason this update is travelling so quickly."
    if "century" in text or "hundred" in text:
        return "Interesting stat: a century changes the match tempo and can define the entire innings."
    if "hat-trick" in text:
        return "Interesting stat: a hat-trick is one of sport's rarest momentum swings and can decide a match in minutes."
    if sport == "football":
        return "Interesting stat: watch the final score, decisive goal timing, clean-sheet angle, and table impact."
    return "Interesting stat: watch runs, wickets, strike rate, economy rate, and whether the chase pressure shaped the finish."


def expand_to_target_length(script: str, item: NewsItem) -> str:
    words = script.split()
    if len(words) >= 175:
        return script
    extras = [
        "For a Short, the angle is simple: explain the result fast, show the pressure moments visually, and give fans one question to answer in comments.",
        "Keep an eye on official scorecards and team announcements, because post-match details can add selection news, injury updates, and milestone confirmations.",
        "This is exactly the kind of story that travels fast: big names, strong fan emotion, and a result or update that can change the next match narrative.",
    ]
    if item.sport == "football":
        extras.append("On the football side, focus the visuals on scoreline cards, player-impact panels, table-race language, and a bold FINAL SCORE moment.")
    else:
        extras.append("On the cricket side, focus the visuals on batting milestones, bowling spells, chase pressure, and a bold WINNER or CENTURY moment.")
    while len(script.split()) < 175:
        script += " " + extras[len(script.split()) % len(extras)]
    return script


def generate_scenes(item: NewsItem, script: str) -> list[dict[str, str]]:
    hook = short_line(item.title, 48)
    keyword = pick_keyword(item)
    return [
        {"scene": "1", "visual": "Breaking sports alert", "text": f"{keyword}: {hook}", "purpose": "3-second hook"},
        {"scene": "2", "visual": "Source and topic card", "text": item.source, "purpose": "Attribution"},
        {"scene": "3", "visual": "Match summary card", "text": short_line(item.summary or item.title, 70), "purpose": "Context"},
        {"scene": "4", "visual": "Final score spotlight", "text": extract_score_line(item.title, item.summary).replace("Final score watch: ", ""), "purpose": "Score"},
        {"scene": "5", "visual": "Key moment animation", "text": "MOMENTUM SWING", "purpose": "Key moment"},
        {"scene": "6", "visual": "Player impact/stat card", "text": infer_stats_line(item.title, item.summary, item.sport), "purpose": "Statistics"},
        {"scene": "7", "visual": "Why it matters", "text": infer_tournament_line(item.title, item.summary, item.sport), "purpose": "Tournament impact"},
        {"scene": "8", "visual": "Call to action", "text": "LIKE • SUBSCRIBE • COMMENT", "purpose": "CTA"},
    ]


async def generate_voice(text: str, output: Path, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate="+12%", pitch="+3Hz")
    await communicate.save(str(output))


def collect_visual_assets(item: NewsItem, assets_dir: Path, limit: int = TARGET_SCENE_COUNT) -> list[ImageAsset]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    assets: list[ImageAsset] = []

    if item.image_url:
        maybe_add_image_asset(
            assets,
            item.image_url,
            assets_dir / "source_rss_image.jpg",
            source=item.source,
            source_url=item.link,
            credit=f"{item.source} RSS media",
            license_text="Source-provided feed image; verify reuse rights before monetized upload.",
            limit=limit,
        )

    for index, image_url in enumerate(extract_article_image_urls(item.link), start=1):
        if len(assets) >= limit:
            break
        maybe_add_image_asset(
            assets,
            image_url,
            assets_dir / f"source_article_image_{index:02d}.jpg",
            source=item.source,
            source_url=item.link,
            credit=f"{item.source} article image",
            license_text="Source article image; verify reuse rights before monetized upload.",
            limit=limit,
        )

    for query in image_search_queries(item):
        if len(assets) >= limit:
            break
        for result in search_commons_images(query, limit=5):
            if len(assets) >= limit:
                break
            if any(existing.source_url == result["page_url"] for existing in assets):
                continue
            maybe_add_image_asset(
                assets,
                result["url"],
                assets_dir / f"commons_{len(assets) + 1:02d}_{slugify(query)[:32]}.jpg",
                source="Wikimedia Commons",
                source_url=result["page_url"],
                credit=result["credit"],
                license_text=result["license"],
                limit=limit,
            )

    while len(assets) < MIN_VISUAL_ASSETS:
        assets.append(create_story_card_asset(item, assets_dir, len(assets) + 1))

    return assets


def maybe_add_image_asset(
    assets: list[ImageAsset],
    url: str,
    destination: Path,
    source: str,
    source_url: str,
    credit: str,
    license_text: str,
    limit: int,
) -> None:
    if len(assets) >= limit or not url:
        return
    normalized_url = url.split("#", 1)[0]
    if any(existing.source_url == source_url and Path(existing.path).name == destination.name for existing in assets):
        return
    if any(existing.source_url == normalized_url for existing in assets):
        return
    asset = download_image_asset(
        normalized_url,
        destination,
        source=source,
        source_url=source_url,
        credit=credit,
        license_text=license_text,
    )
    if asset:
        assets.append(asset)


def extract_article_image_urls(article_url: str, limit: int = 6) -> list[str]:
    if not article_url:
        return []
    try:
        response = requests.get(article_url, timeout=20, headers={"User-Agent": "SportsShortsBot/1.0"})
        response.raise_for_status()
    except Exception:
        return []
    candidates: list[str] = []
    meta_patterns = [
        r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image|twitter:image:src)["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image|twitter:image:src)["\']',
    ]
    for pattern in meta_patterns:
        candidates.extend(re.findall(pattern, response.text, flags=re.IGNORECASE))
    candidates.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', response.text, flags=re.IGNORECASE))

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        image_url = html.unescape(candidate.strip())
        if not image_url or image_url.startswith("data:"):
            continue
        image_url = urljoin(article_url, image_url)
        key = image_url.split("?", 1)[0]
        if key in seen or not is_supported_image_url(image_url):
            continue
        seen.add(key)
        deduped.append(image_url)
        if len(deduped) >= limit:
            break
    return deduped


def create_story_card_asset(item: NewsItem, assets_dir: Path, index: int) -> ImageAsset:
    bg, accent, secondary, text_color = PALETTES[(index - 1) % len(PALETTES)]
    card = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(card, "RGBA")
    for y in range(0, HEIGHT, 16):
        blend = y / HEIGHT
        draw.rectangle((0, y, WIDTH, y + 16), fill=mix_hex(bg, secondary if index % 2 else accent, blend * 0.35))
    draw.rounded_rectangle((56, 112, 1024, 1800), radius=8, fill=(0, 0, 0, 130))
    draw.rectangle((96, 180, 984, 208), fill=accent)
    draw.text((96, 270), "LATEST SPORTS UPDATE", font=font(54, bold=True), fill=accent)
    draw.text((96, 365), item.source.upper(), font=font(34, bold=True), fill=text_color)

    y = 560
    for line in wrap_text(short_line(item.title, 120), font(82, bold=True), 880)[:6]:
        draw.text((96, y), line, font=font(82, bold=True), fill=text_color)
        y += 100
    y = max(y + 70, 1180)
    for line in wrap_text(short_line(item.summary or item.title, 220), font(42), 880)[:5]:
        draw.text((96, y), line, font=font(42), fill=text_color)
        y += 58

    published = "Latest"
    if item.published:
        try:
            published = datetime.fromisoformat(item.published).astimezone().strftime("%d %b %Y")
        except Exception:
            published = "Latest"
    draw.rounded_rectangle((96, 1608, 520, 1680), radius=8, fill=accent)
    draw.text((126, 1622), published.upper(), font=font(34, bold=True), fill="#0A0A0A")
    draw.text((96, 1718), f"Visual {index:02d}", font=font(30), fill=text_color)

    destination = assets_dir / f"generated_latest_card_{index:02d}.jpg"
    card.save(destination, "JPEG", quality=96, subsampling=0, optimize=True)
    return ImageAsset(
        str(destination.resolve()),
        "Generated latest-story card",
        item.link,
        "Sports Shorts Pipeline",
        "Generated original visual from current story metadata.",
    )


def image_search_queries(item: NewsItem) -> list[str]:
    text = f"{item.title} {item.summary}"
    queries: list[str] = []
    expansions = {
        "RCB": ["Royal Challengers Bangalore", "Royal Challengers Bangalore players"],
        "CSK": ["Chennai Super Kings"],
        "MI": ["Mumbai Indians"],
        "KKR": ["Kolkata Knight Riders"],
        "SRH": ["Sunrisers Hyderabad"],
        "DC": ["Delhi Capitals"],
        "GT": ["Gujarat Titans"],
        "LSG": ["Lucknow Super Giants"],
        "RR": ["Rajasthan Royals"],
        "PBKS": ["Punjab Kings"],
        "PSG": ["Paris Saint-Germain F.C.", "Paris Saint-Germain players"],
        "UCL": ["UEFA Champions League"],
        "WC": ["World Cup"],
    }
    for short, expanded_queries in expansions.items():
        if re.search(rf"\b{re.escape(short)}\b", text, flags=re.IGNORECASE):
            queries.extend(expanded_queries)

    named_phrases = re.findall(r"(?:[A-Z][A-Za-z'.-]+|[A-Z]{2,})(?:\s+(?:[A-Z][A-Za-z'.-]+|[A-Z]{2,})){0,3}", text)
    named_phrases = sorted(named_phrases, key=lambda phrase: (len(phrase.split()), len(phrase)), reverse=True)
    competition_phrases: list[str] = []
    for phrase in named_phrases:
        cleaned = clean_text(phrase)
        if len(cleaned) < 4 or cleaned.lower() in {"big", "source"}:
            continue
        if is_competition_phrase(cleaned):
            competition_phrases.append(cleaned)
        else:
            queries.append(cleaned)

    queries.extend(competition_phrases)
    queries.append(item.title)
    queries.append(f"{item.title} {item.sport}")
    if item.sport == "cricket":
        queries.append("cricket match")
    else:
        queries.append("football match")

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = normalize_key(query)
        if normalized and normalized not in seen:
            deduped.append(query)
            seen.add(normalized)
    return deduped[:10]


def is_competition_phrase(value: str) -> bool:
    lowered = value.lower()
    competition_terms = ["champions", "league", "world cup", "ipl", "icc", "fifa", "uefa", "final"]
    return any(term in lowered for term in competition_terms)


def search_commons_images(query: str, limit: int = 3) -> list[dict[str, str]]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "format": "json",
        "formatversion": "2",
    }
    try:
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params=params,
            timeout=20,
            headers={"User-Agent": "SportsShortsBot/1.0 (local automated sports video pipeline)"},
        )
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", [])
    except Exception:
        return []

    results: list[dict[str, str]] = []
    for page in pages:
        imageinfo = (page.get("imageinfo") or [{}])[0]
        url = imageinfo.get("url", "")
        if not is_supported_image_url(url):
            continue
        metadata = imageinfo.get("extmetadata", {})
        credit = clean_text(metadata.get("Artist", {}).get("value", "")) or page.get("title", "Wikimedia Commons")
        license_text = clean_text(metadata.get("LicenseShortName", {}).get("value", "")) or "Wikimedia Commons"
        description_url = imageinfo.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{page.get('title', '').replace(' ', '_')}"
        results.append(
            {
                "url": url,
                "page_url": description_url,
                "credit": credit,
                "license": license_text,
                "title": page.get("title", ""),
                "width": str(imageinfo.get("width", 0)),
                "height": str(imageinfo.get("height", 0)),
            }
        )
    query_tokens = meaningful_tokens(query)
    return sorted(
        results,
        key=lambda result: (
            len(query_tokens & meaningful_tokens(result.get("title", ""))),
            int(result.get("width", "0")) * int(result.get("height", "0")),
        ),
        reverse=True,
    )


def download_image_asset(
    url: str,
    destination: Path,
    source: str,
    source_url: str,
    credit: str,
    license_text: str,
) -> ImageAsset | None:
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "SportsShortsBot/1.0"})
        response.raise_for_status()
        destination.write_bytes(response.content)
        with Image.open(destination) as img:
            img = img.convert("RGB")
            if img.width < 640 or img.height < 360:
                destination.unlink(missing_ok=True)
                return None
            img.thumbnail((2600, 2600), Image.Resampling.LANCZOS)
            img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))
            img.save(destination, "JPEG", quality=96, subsampling=0, optimize=True)
    except Exception:
        destination.unlink(missing_ok=True)
        return None
    return ImageAsset(str(destination.resolve()), source, source_url, credit, license_text)


def is_supported_image_url(url: str) -> bool:
    return bool(re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", url, flags=re.IGNORECASE))


def render_scene_images(item: NewsItem, scenes: list[dict[str, str]], package_dir: Path, visual_assets: list[ImageAsset]) -> list[Path]:
    paths: list[Path] = []
    palette = PALETTES[int(hashlib.sha1(item.title.encode()).hexdigest(), 16) % len(PALETTES)]
    for index, scene in enumerate(scenes, start=1):
        asset = visual_assets[(index - 1) % len(visual_assets)] if visual_assets else None
        image = make_scene_image(item, scene, palette, index, len(scenes), asset)
        path = package_dir / f"scene_{index:02d}.png"
        image.save(path)
        paths.append(path)
    return paths


def make_scene_image(
    item: NewsItem,
    scene: dict[str, str],
    palette: tuple[str, str, str, str],
    index: int,
    scene_count: int,
    asset: ImageAsset | None = None,
) -> Image.Image:
    bg, accent, secondary, text_color = palette
    image = make_photo_background(asset, bg, secondary)
    draw = ImageDraw.Draw(image, "RGBA")
    random.seed(hashlib.md5(f"{item.title}{index}".encode()).hexdigest())

    if not asset:
        for y in range(0, HEIGHT, 12):
            blend = y / HEIGHT
            color = mix_hex(bg, secondary if index % 2 else accent, blend * 0.28)
            draw.rectangle((0, y, WIDTH, y + 12), fill=color)

    if not asset:
        for _ in range(16):
            x = random.randint(-160, WIDTH)
            y = random.randint(-160, HEIGHT)
            size = random.randint(120, 380)
            color = accent if random.random() > 0.5 else secondary
            overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            odraw.rectangle((x, y, x + size, y + 8), fill=hex_to_rgba(color, 58))
            overlay = overlay.filter(ImageFilter.GaussianBlur(2))
            image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(image, "RGBA")

    title_font = font(86, bold=True)
    mid_font = font(54, bold=True)
    small_font = font(34)
    tag_font = font(30, bold=True)

    sport_label = "FOOTBALL" if item.sport == "football" else "CRICKET"
    draw.rounded_rectangle((64, 70, 362, 132), radius=8, fill=accent)
    draw.text((88, 84), sport_label, font=tag_font, fill="#0A0A0A")
    draw.rounded_rectangle((52, 145, 1028, 184), radius=8, fill=(0, 0, 0, 130))
    draw.text((64, 150), scene["visual"].upper(), font=small_font, fill=text_color)

    main_text = clean_visual_text(scene["text"])
    draw.rounded_rectangle((44, 390, 1036, 1120), radius=8, fill=(0, 0, 0, 150))
    if index == 1:
        lines = wrap_text(main_text, title_font, 900)
        y = 460
        for line in lines[:5]:
            draw.text((64, y), line, font=title_font, fill=text_color)
            y += 104
    else:
        lines = wrap_text(main_text, mid_font, 900)
        y = 430
        for line in lines[:8]:
            draw.text((64, y), line, font=mid_font, fill=text_color)
            y += 72

    draw.rounded_rectangle((44, 1465, 1036, 1680), radius=8, fill=(0, 0, 0, 155))
    draw.rectangle((64, 1490, 1016, 1510), fill=accent)
    draw.text((64, 1545), short_line(item.title, 62), font=small_font, fill=text_color)
    draw.text((64, 1615), f"Source: {item.source}", font=small_font, fill=text_color)
    if asset:
        draw.text((64, 1668), f"Image: {short_line(asset.source, 38)}", font=font(24), fill=text_color)
    draw.text((64, 1740), f"{index:02d}/{scene_count:02d}", font=font(42, bold=True), fill=accent)
    return image


def make_photo_background(asset: ImageAsset | None, bg: str, secondary: str) -> Image.Image:
    if not asset:
        return Image.new("RGB", (WIDTH, HEIGHT), bg)
    try:
        with Image.open(asset.path) as raw:
            image = raw.convert("RGB")
    except Exception:
        return Image.new("RGB", (WIDTH, HEIGHT), bg)
    image = cover_resize(image, WIDTH, HEIGHT)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=3))
    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 70))
    tint = Image.new("RGBA", (WIDTH, HEIGHT), hex_to_rgba(secondary, 18))
    return Image.alpha_composite(Image.alpha_composite(image.convert("RGBA"), shade), tint).convert("RGB")


def cover_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    new_size = (math.ceil(image.width * scale), math.ceil(image.height * scale))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def render_video(scene_paths: list[Path], audio_path: Path, video_path: Path, duration: float) -> None:
    scene_duration = duration / len(scene_paths)
    concat_file = video_path.parent / "scenes.txt"
    lines: list[str] = []
    for scene_path in scene_paths:
        lines.append(f"file '{scene_path.resolve().as_posix()}'")
        lines.append(f"duration {scene_duration:.3f}")
    lines.append(f"file '{scene_paths[-1].resolve().as_posix()}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    silent_video = video_path.parent / "silent.mp4"
    intro_fade = "fade=t=in:st=0:d=0.35"
    outro_fade = f"fade=t=out:st={max(0.5, duration - 0.45):.2f}:d=0.35"
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-t",
            f"{duration:.3f}",
            "-vf",
            f"scale=1080:1920:flags=lanczos,fps=30,format=yuv420p,{intro_fade},{outro_fade}",
            "-an",
            str(silent_video),
        ]
    )

    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-af",
            "apad",
            "-t",
            f"{duration:.3f}",
            "-movflags",
            "+faststart",
            str(video_path),
        ]
    )


def run_ffmpeg(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def make_srt(text: str, duration: float) -> str:
    chunks = chunk_words(text.split(), 8)
    if not chunks:
        return ""
    seconds_per_chunk = duration / len(chunks)
    lines = []
    for index, words in enumerate(chunks, start=1):
        start = (index - 1) * seconds_per_chunk
        end = min(duration, index * seconds_per_chunk)
        caption = highlight_keywords(" ".join(words))
        lines.append(f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{caption}\n")
    return "\n".join(lines)


def highlight_keywords(text: str) -> str:
    for word in IMPORTANT_WORDS:
        text = re.sub(rf"\b{re.escape(word)}\b", word, text, flags=re.IGNORECASE)
    return text


def srt_time(seconds: float) -> str:
    ms = int((seconds - int(seconds)) * 1000)
    whole = int(seconds)
    h = whole // 3600
    m = (whole % 3600) // 60
    s = whole % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_video_title(item: NewsItem) -> str:
    prefix = "Football" if item.sport == "football" else "Cricket"
    title = f"{prefix}: {item.title}"
    return short_line(title, 96)


def generate_description(item: NewsItem) -> str:
    summary = item.summary or item.title
    return (
        f"{summary}\n\n"
        f"Source: {item.source}\n{item.link}\n\n"
        "Daily football and cricket Shorts with match results, records, transfers, milestones, and breaking sports news. "
        "Like, subscribe, and comment your player of the match."
    )


def generate_hashtags(item: NewsItem) -> list[str]:
    base = ["#SportsNews", "#MatchHighlights", "#YouTubeShorts"]
    if item.sport == "football":
        sport_tags = ["#Football", "#PremierLeague", "#ChampionsLeague", "#FIFA"]
    else:
        sport_tags = ["#Cricket", "#IPL", "#ICC", "#InternationalCricket"]
    text = f"{item.title} {item.summary}".lower()
    if "transfer" in text:
        sport_tags.append("#TransferNews")
    if "record" in text:
        sport_tags.append("#Record")
    return sport_tags + base


def generate_thumbnail_text(item: NewsItem) -> str:
    keyword = pick_keyword(item)
    return f"{keyword}\n{short_line(item.title, 42)}"


def pick_keyword(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}".lower()
    if "century" in text or "hundred" in text:
        return "CENTURY"
    if "hat-trick" in text:
        return "HAT-TRICK"
    if "record" in text:
        return "RECORD"
    if "transfer" in text or "sign" in text:
        return "TRANSFER"
    if "win" in text or "beat" in text:
        return "WINNER"
    if "goal" in text:
        return "GOAL"
    return "BREAKING"


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()


def meaningful_tokens(value: str) -> set[str]:
    stopwords = {
        "file",
        "jpg",
        "jpeg",
        "png",
        "webp",
        "the",
        "and",
        "for",
        "with",
        "from",
        "news",
        "match",
        "sports",
        "sport",
    }
    return {
        token
        for token in normalize_key(value).split()
        if len(token) >= 3 and token not in stopwords
    }


def slugify(value: str) -> str:
    value = normalize_key(value)
    return re.sub(r"\s+", "-", value) or "sports-short"


def unique_dir(parent: Path, name: str) -> Path:
    candidate = parent / name
    suffix = 2
    while candidate.exists():
        candidate = parent / f"{name}-{suffix}"
        suffix += 1
    return candidate


def unique_file(parent: Path, name: str) -> Path:
    stem = Path(name).stem
    suffix_text = Path(name).suffix or ".mp4"
    candidate = parent / f"{stem}{suffix_text}"
    suffix = 2
    while candidate.exists():
        candidate = parent / f"{stem}-{suffix}{suffix_text}"
        suffix += 1
    return candidate


def short_line(value: str, limit: int) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def clean_visual_text(value: str) -> str:
    return re.sub(r"https?://\S+", "", clean_text(value)).replace("•", "|")


def wrap_text(text: str, text_font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    probe = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(probe)
    for word in words:
        candidate = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=text_font)
        if bbox[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default(size=size)


def hex_to_rgba(value: str, alpha: int) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha


def mix_hex(a: str, b: str, amount: float) -> str:
    ar, ag, ab, _ = hex_to_rgba(a, 255)
    br, bg, bb, _ = hex_to_rgba(b, 255)
    amount = clamp(amount, 0, 1)
    r = round(ar + (br - ar) * amount)
    g = round(ag + (bg - ag) * amount)
    bl = round(ab + (bb - ab) * amount)
    return f"#{r:02x}{g:02x}{bl:02x}"


def chunk_words(words: list[str], size: int) -> list[list[str]]:
    return [words[i : i + size] for i in range(0, len(words), size)]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


if __name__ == "__main__":
    main()

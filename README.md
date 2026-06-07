# AI Sports Shorts Pipeline

This project generates at least 10 ready-to-upload YouTube Shorts per run for football and cricket using free sources and local rendering.

## What it does

- Fetches current sports stories from free public RSS feeds.
- Prioritizes football and cricket topics from the last 24 hours when available.
- Creates unique scripts, titles, descriptions, hashtags, scene plans, and thumbnails.
- Searches for directly related, higher-resolution article, team, player, and topic images from RSS media, article pages, and Wikimedia Commons.
- Ensures every Short has at least 7 distinct current-story visual assets, using generated latest-story cards if public sources return fewer images.
- Generates energetic AI narration with free Edge TTS.
- Creates sharp 1080x1920 vertical news visuals locally with Pillow.
- Exports clean MP4 videos with voice narration only.
- Saves a complete metadata bundle for each Short.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

FFmpeg must be installed and available on `PATH`. It is already available in this workspace.

## Run

```powershell
python sports_shorts_pipeline.py --count 10
```

Outputs are written to:

```text
output/YYYYMMDD_HHMMSS/
```

Each generated Short folder contains:

- a descriptively named MP4, also copied into `videos/` for easy upload
- `metadata.json`
- `visual_assets.json`
- `script.txt`
- `voiceover.txt`
- `scene_breakdown.txt`
- generated visual scene PNGs

## Upload and schedule to YouTube

1. In Google Cloud, enable the YouTube Data API v3.
2. Create an OAuth client of type `Desktop app`.
3. Download the OAuth JSON and save it in this folder as:

```text
client_secret.json
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Generate, upload, and schedule Shorts:

```powershell
python sports_shorts_pipeline.py --count 10
```

By default, each Short is uploaded immediately after it is created. The first Short is scheduled at least 20 minutes after upload, and every next Short is scheduled at least 20 minutes after the previous scheduled publish time. To choose the first publish time:

```powershell
python sports_shorts_pipeline.py --count 10 --schedule-start "2026-06-01T10:00:00+05:30" --schedule-interval-minutes 20
```

Upload results are saved to:

```text
output/YYYYMMDD_HHMMSS/youtube_uploads.json
```

The first OAuth run opens a browser for channel authorization. Later runs reuse `token.json`.

Duplicate protection is stored in `.sports_shorts_state.json`. The pipeline skips topics, source URLs, and local video hashes it has already uploaded. After each successful YouTube upload, the local MP4 copies are deleted. After each run, older timestamped output folders are deleted automatically; the current run metadata, state file, and OAuth token are kept. For testing without upload:

```powershell
python sports_shorts_pipeline.py --count 10 --no-upload-youtube
```

Important: YouTube upload quota is controlled by your Google Cloud project. The official YouTube Data API quota calculator lists `videos.insert` as a high-cost upload endpoint, so 10 automated uploads per day may require enough daily quota on your project.

## Notes on rights and accuracy

The pipeline uses public news summaries and related still images from RSS media and Wikimedia Commons rather than downloading copyrighted match footage. Team logos are represented as text badges by default to avoid rights issues. Scripts include source attribution and avoid inventing scores when a source item does not provide them. Check `visual_assets.json` for image credits and license notes before publishing monetized videos.

For higher accuracy, add official league or tournament API fetchers in `fetch_sports_news()`. The current version is built to run without paid services.

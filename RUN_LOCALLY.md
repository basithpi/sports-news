# Run YouTube Shorts Pipeline on Your Laptop

This guide shows how to generate and upload shorts **manually on your laptop** (without waiting for daily GitHub automation).

---

## ✅ Prerequisites

Make sure you have:
- ✓ Python 3.11+ installed
- ✓ FFmpeg installed
- ✓ Your Google OAuth credentials (client_secret.json)
- ✓ This code cloned/downloaded

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Python Dependencies

```powershell
cd "c:\Users\basit\Music\sports video"

# Create virtual environment (one-time)
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Add Your Google Credentials

Copy your `client_secret.json` to this folder:
```
c:\Users\basit\Music\sports video\client_secret.json
```

### Step 3: Run the Pipeline

**Generate 15 shorts:**
```powershell
python sports_shorts_pipeline.py --count 15
```

**Generate and upload to YouTube:**
```powershell
python sports_shorts_pipeline.py --count 15
```

First time will open browser for YouTube authorization ✓

---

## 📋 Common Commands

### Generate shorts without uploading (test)
```powershell
python sports_shorts_pipeline.py --count 15 --no-upload-youtube
```

### Generate fewer shorts
```powershell
python sports_shorts_pipeline.py --count 5
```

### Upload with custom schedule
```powershell
python sports_shorts_pipeline.py --count 15 --schedule-start "2026-06-08T09:00:00+05:30" --schedule-interval-minutes 20
```

### View all options
```powershell
python sports_shorts_pipeline.py --help
```

---

## 📁 Output Location

Shorts are saved to:
```
output\YYYYMMDD_HHMMSS\
```

Each folder contains:
- `video.mp4` - The shorts video
- `metadata.json` - Video info
- `script.txt` - AI script
- `visual_assets.json` - Image credits
- `youtube_uploads.json` - Upload status

---

## 🔐 First Run Setup

**First run will:**
1. Generate 15 shorts from sports news
2. Show YouTube authorization in browser
3. Upload all 15 to your channel
4. Save `token.json` for future runs

**After first run:**
- Token is saved, no more authorization needed
- Just run the command again anytime

---

## ⏱️ How Long Does It Take?

| Task | Time |
|------|------|
| Generate 15 shorts | 5-10 minutes |
| Upload to YouTube | 2-5 minutes |
| **Total** | **7-15 minutes** |

---

## 🐛 Troubleshooting

### "FFmpeg not found"
Install FFmpeg:
1. Download from: https://ffmpeg.org/download.html
2. Add to your PATH environment variable

**Or install via Chocolatey:**
```powershell
choco install ffmpeg
```

### "ModuleNotFoundError: No module named 'edge_tts'"
Reinstall dependencies:
```powershell
pip install --upgrade -r requirements.txt
```

### "Google credentials not found"
Make sure `client_secret.json` is in this folder:
```
c:\Users\basit\Music\sports video\client_secret.json
```

### "YouTube quota exceeded"
You've hit the daily quota. Wait 24 hours or:
1. Request quota increase in Google Cloud Console
2. Or reduce `--count` to 6 shorts/day

### "OAuth token expired"
Delete `token.json` and run again:
```powershell
rm token.json
python sports_shorts_pipeline.py --count 15
```

---

## 💡 Tips

1. **Keep virtual environment active** - Always run `.\.venv\Scripts\Activate.ps1` first
2. **Check internet connection** - Needs to fetch sports news and upload to YouTube
3. **Keep credentials safe** - Never share `client_secret.json`
4. **Monitor quota** - Check Google Cloud Console for quota usage

---

## 🔄 Workflow

```
1. Run command
   ↓
2. Generate 15 shorts (5-10 min)
   ↓
3. Browser opens for YouTube auth (first time only)
   ↓
4. Upload to YouTube (2-5 min)
   ↓
5. Videos scheduled to publish
   ↓
6. Done! Check your YouTube channel
```

---

## 📊 Options Reference

```powershell
# Count - how many shorts (default: 10)
--count 15

# No upload - test mode (don't upload to YouTube)
--no-upload-youtube

# Schedule start - when to publish first video (ISO format)
--schedule-start "2026-06-08T09:00:00+05:30"

# Schedule interval - minutes between uploads (min 15)
--schedule-interval-minutes 20

# Help - show all options
--help
```

---

## ✨ Examples

**Example 1: Generate 10 shorts, test mode**
```powershell
python sports_shorts_pipeline.py --count 10 --no-upload-youtube
```

**Example 2: Generate 15 shorts, publish 8 AM - 12:50 PM**
```powershell
python sports_shorts_pipeline.py --count 15 --schedule-start "2026-06-08T08:00:00+05:30" --schedule-interval-minutes 15
```

**Example 3: Generate 6 shorts, publish starting 6 PM**
```powershell
python sports_shorts_pipeline.py --count 6 --schedule-start "2026-06-08T18:00:00+05:30" --schedule-interval-minutes 20
```

---

## 🎯 Run It Daily

To run this **every day at 7 AM** on your laptop, add a Windows Task:

1. **Open Task Scheduler** (search "Task Scheduler")
2. **Create Task:**
   - Name: "Daily Shorts Upload"
   - Trigger: Daily at 7:00 AM
   - Action: Run `C:\Python\python.exe`
   - Arguments: `C:\Users\basit\Music\sports video\sports_shorts_pipeline.py --count 15`
   - Working directory: `C:\Users\basit\Music\sports video`

Or use this PowerShell script to create it:
```powershell
# Save as create-task.ps1
$taskName = "Daily Shorts Upload"
$scriptPath = "C:\Users\basit\Music\sports video\sports_shorts_pipeline.py"
$pythonPath = "C:\Users\basit\AppData\Local\Programs\Python\Python314\python.exe"

$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "$scriptPath --count 15" -WorkingDirectory "C:\Users\basit\Music\sports video"
$trigger = New-ScheduledTaskTrigger -Daily -At 7AM
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -RunLevel Highest
```

Run it:
```powershell
powershell -ExecutionPolicy Bypass -File create-task.ps1
```

---

## 📞 Need Help?

- Check `GITHUB_SETUP.md` for GitHub Actions setup
- View `QUICK_START.md` for quick reference
- See `CONFIG_EXAMPLES.md` for more examples

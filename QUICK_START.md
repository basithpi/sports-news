# Quick Reference: Daily YouTube Shorts Automation

## ✅ What You'll Get

- ✓ **Automatic daily generation** of sports shorts (football & cricket)
- ✓ **Automatic YouTube upload** of 15 shorts per day
- ✓ **Smart scheduling** - uploads spread throughout the day
- ✓ **No manual work** - runs on GitHub's servers 24/7
- ✓ **Duplicate protection** - avoids uploading same story twice
- ✓ **Secure credentials** - Google OAuth stored in encrypted GitHub Secrets

## 📋 Setup in 5 Minutes

### 1️⃣ Get Google OAuth Credentials
```
Google Cloud Console → Create Project → Enable YouTube Data API v3
→ Create OAuth 2.0 Client (Desktop) → Download JSON
```

### 2️⃣ Add to GitHub Secrets
```
GitHub Repo Settings → Secrets → New Secret
Name: GOOGLE_CLIENT_SECRET
Value: (paste entire JSON)
```

### 3️⃣ Request YouTube Quota Increase
```
⚠️ CRITICAL: 15 shorts/day needs ~24,000 quota (default is 10,000)
Google Cloud Console → Quotas → YouTube Data API v3 → Request increase
Approval: 24-48 hours
```

### 4️⃣ Run First Upload
```
GitHub Repo → Actions → Daily YouTube Shorts Upload → Run workflow
(one-time OAuth authorization required, then automatic)
```

## 🎛️ Configuration

### Change Upload Count
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
--count 15  # Change to 10 (safe), 20 (needs more quota), etc.
```

### Change Schedule Time
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
- cron: '30 2 * * *'  # 02:30 UTC = 8:00 AM IST
```

Common times:
- `0 8 * * *` = 8:00 AM UTC
- `30 3 * * *` = 3:30 AM UTC (9:00 AM IST)
- `0 12 * * 1-5` = Weekdays only at noon UTC

Use [crontab.guru](https://crontab.guru) to verify.

### Change Publish Time
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
--schedule-start "2026-06-08T09:00:00+05:30"
--schedule-interval-minutes 15  # Gap between uploads (min 15)
```

## 📊 Quota Calculator

YouTube API Quota per upload:
- Video insert: ~1,600 units
- 15 shorts/day: ~24,000 units needed
- Default quota: 10,000 units/day

**Options:**
1. **Request increase** to 50,000/day (RECOMMENDED)
2. **Upload 6 shorts/day** (safe with default quota)
3. **Upload alternate days** (cron: `30 2 * * 0,2,4`)
4. **Buy quota** (enterprise option)

## 🔐 Security

✅ **Safe:**
- Credentials stored as GitHub Secrets (encrypted)
- Auto-deleted after workflow runs
- Repository access controlled

⚠️ **Important:**
- Keep repository **PRIVATE**
- Don't commit `client_secret.json`
- Monitor quota usage regularly

## 📱 Monitor & Control

### View Uploads
```
GitHub → Actions tab → See all runs and logs
```

### Manual Upload (Anytime)
```
GitHub → Actions → Daily YouTube Shorts Upload → Run workflow
```

### Disable Auto-Upload (Testing)
```
Add flag to workflow: --no-upload-youtube
This generates shorts but doesn't upload to YouTube
```

## 🔧 Customization

### Sports Priority
Edit `sports_shorts_pipeline.py` → `RSS_FEEDS` to add/remove sources

### Video Length
Edit `sports_shorts_pipeline.py` → `MIN_DURATION`, `MAX_DURATION` (default: 60-120 sec)

### Visual Assets
Edit `sports_shorts_pipeline.py` → `MIN_VISUAL_ASSETS` (default: 7 images/short)

## ❌ Troubleshooting

### "Insufficient quota"
→ Request quota increase in Google Cloud Console (24-48 hours)

### "OAuth token expired"
→ Delete artifact in Actions, next run will ask for new auth

### Workflow doesn't trigger
→ Check Actions tab for errors
→ Ensure repository has Actions enabled

### Videos not uploading
→ Check workflow logs in Actions tab
→ Verify YouTube channel is authorized

## 📞 Support

- **Logs**: GitHub Actions → Daily YouTube Shorts Upload → View logs
- **Status**: Check "state.json" for previously uploaded videos
- **Queue**: Videos publish staggered (15 min apart by default)

---

**Next Step:** Run `SETUP_CHECKLIST.ps1` to walk through full setup!

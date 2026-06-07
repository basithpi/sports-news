# 🚀 GitHub Actions Daily YouTube Shorts Automation - Setup Complete!

## ✅ What Was Created

I've set up a complete automated system for uploading **15 YouTube shorts daily** using GitHub Actions. Here's what's ready:

### 📁 New Files Created

```
.github/workflows/
  └── daily-shorts-upload.yml       # GitHub Actions workflow (runs daily at 8 AM IST)
.gitignore                           # Protects sensitive files from being committed
GITHUB_SETUP.md                      # Detailed setup guide with troubleshooting
QUICK_START.md                       # Quick reference guide (READ THIS FIRST)
CONFIG_EXAMPLES.md                   # Configuration examples for different scenarios
SETUP_CHECKLIST.ps1                  # Step-by-step setup guide
VALIDATE_SETUP.ps1                   # Validation tool to verify setup
```

---

## 🎯 What This Does

✅ **Every day at 8:00 AM IST:**
- Generates 15 YouTube shorts from sports news (football & cricket)
- Uploads all 15 to your YouTube channel
- Publishes them staggered (every 15 minutes)
- No manual work needed

✅ **Secure:**
- Google credentials stored as encrypted GitHub Secrets
- OAuth token auto-managed by GitHub Actions
- No sensitive data in your repository

✅ **Flexible:**
- Change upload time, count, and schedule easily
- Manual trigger available anytime
- Test mode available without uploading

---

## 📋 Quick Setup (5 Steps)

### 1. Get Google OAuth Credentials (5 min)
```
1. Go to: https://console.cloud.google.com
2. Create a project (or use existing)
3. Enable YouTube Data API v3
4. Create OAuth 2.0 Client (Desktop Application)
5. Download the JSON file
```

### 2. Create GitHub Repository (3 min)
```bash
# Push your code to GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO
git branch -M main
git commit -m "Add daily YouTube shorts automation"
git push -u origin main
```

### 3. Add GitHub Secrets (2 min)
```
GitHub Settings → Secrets and variables → Actions
New Secret:
  Name: GOOGLE_CLIENT_SECRET
  Value: [Paste entire JSON from step 1]
```

### 4. Request YouTube Quota (1 min)
⚠️ **IMPORTANT**: 15 shorts/day needs ~24,000 quota units
- Default quota: 10,000 units/day (NOT ENOUGH)
- Request increase to: 50,000 units/day

```
Google Cloud Console → Quotas
Search: YouTube Data API v3
Click: Videos: insert quota
Request increase to: 50,000 units/day
(Approval: 24-48 hours)
```

### 5. Trigger First Run (2 min)
```
GitHub → Actions → Daily YouTube Shorts Upload
Click: Run workflow
(First run needs browser authorization - one-time only)
```

**Total time: ~15 minutes ⏱️**

---

## 🔧 Configuration

### Change Upload Time
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
- cron: '30 2 * * *'  # 02:30 UTC = 8:00 AM IST
```
Common times:
- `0 8 * * *` = 8:00 AM UTC
- `0 12 * * *` = 12:00 PM UTC (noon)
- `30 2 * * 1-5` = Weekdays only (Mon-Fri)

### Change Daily Count
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
--count 15  # Change to 10, 20, etc.
```

### Change Publish Schedule
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
--schedule-start "2026-06-08T08:00:00+05:30"  # When to start publishing
--schedule-interval-minutes 15                  # Gap between uploads (min 15)
```

**See CONFIG_EXAMPLES.md for more options**

---

## 🔐 Security Checklist

✅ **Google credentials:**
- [ ] Added to GitHub Secrets (encrypted)
- [ ] NOT committed to repository
- [ ] client_secret.json auto-deleted after runs

✅ **OAuth token:**
- [ ] Saved as GitHub artifact (private)
- [ ] Auto-refreshed before expiration
- [ ] Retained for 90 days

✅ **Repository:**
- [ ] Set to PRIVATE (recommended)
- [ ] .gitignore protects sensitive files

---

## 📊 Daily Workflow

What happens automatically at **8:00 AM IST**:

```
1. GitHub Actions starts workflow
   ↓
2. Checkout latest code
   ↓
3. Install Python dependencies
   ↓
4. Install FFmpeg
   ↓
5. Create credentials from GitHub Secrets
   ↓
6. Generate 15 shorts (videos + metadata)
   ↓
7. Upload 15 shorts to YouTube
   ↓
8. Schedule publishes (every 15 min)
   ↓
9. Save OAuth token for next run
   ↓
10. Delete sensitive credentials
   ↓
Done! Videos publish 8:20 AM - 12:55 PM IST
```

---

## 📱 Monitor & Control

### Check Status
```
GitHub → Actions tab → See all workflow runs
```

### View Logs
```
Actions → Daily YouTube Shorts Upload → Latest run → Click job → Scroll logs
```

### Manual Upload (Anytime)
```
Actions → Daily YouTube Shorts Upload → Run workflow (yellow button)
```

### Disable Automatic Run (Temporarily)
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
on:
  schedule: []  # Remove cron schedule
  workflow_dispatch:
```

---

## 🎬 YouTube Quota Details

Each video upload costs ~1,600 quota units:
- 15 shorts/day × 1,600 = **24,000 units needed**
- Default quota: 10,000 units/day ❌ (NOT ENOUGH)
- Recommended: Request 50,000 units/day ✅

**How to request increase:**
```
Google Cloud Console → APIs & Services → Quotas
Search: YouTube Data API v3
Click: Videos: insert
Click pencil icon → Request increase to 50,000
Approval time: 24-48 hours
```

**If quota denied:**
- Reduce to 6 shorts/day (9,600 units - safe with default)
- Upload on alternate days (cron: `30 2 * * 0,2,4`)
- Contact Google Cloud support

---

## 🚨 Troubleshooting

### Workflow doesn't start
→ Check Actions tab for syntax errors
→ Ensure GitHub Actions is enabled in repository

### "Insufficient quota"
→ Request quota increase (24-48 hours)
→ Temporarily reduce `--count` in workflow

### OAuth token expired
→ Delete the `google-token` artifact in Actions
→ Next workflow run will request new auth

### Videos not uploading
→ Check workflow logs in Actions tab
→ Verify YouTube channel is authorized
→ Check OAuth token validity

### See GITHUB_SETUP.md for more solutions

---

## 📚 Documentation Guide

| File | Purpose |
|------|---------|
| **QUICK_START.md** | Fast reference (READ FIRST) |
| **GITHUB_SETUP.md** | Detailed setup + troubleshooting |
| **CONFIG_EXAMPLES.md** | Configuration scenarios |
| **SETUP_CHECKLIST.ps1** | Step-by-step checklist |
| **.github/workflows/daily-shorts-upload.yml** | Automation workflow |

---

## ✨ Features Included

- ✅ Daily automatic generation & upload
- ✅ 15 shorts per day
- ✅ Smart scheduling (staggered publishes)
- ✅ Duplicate prevention
- ✅ Secure credential management
- ✅ OAuth token auto-refresh
- ✅ Failure notifications
- ✅ Manual trigger capability
- ✅ Full logging & debugging

---

## 🎯 Next Steps

1. **Read QUICK_START.md** (5 min)
2. **Get Google OAuth credentials** (5 min)
3. **Push to GitHub** (2 min)
4. **Add GitHub Secrets** (2 min)
5. **Request YouTube quota** (1 min) ⚠️ DO THIS!
6. **Run first workflow** (2 min)
7. **Verify shorts on YouTube** (2 min)

**Total: ~15 minutes to full automation** ⏱️

---

## 💡 Tips

- 🎬 First run takes longer (OAuth authorization)
- 📊 Monitor quota usage in Google Cloud Console
- 🔄 Token auto-refreshes (you don't need to do anything)
- 🌍 Cron times are in UTC (convert from your timezone)
- 📝 Check logs if something fails (Actions tab → Logs)
- 🚀 You can manually trigger uploads anytime

---

## 📞 Support Resources

- GitHub Actions Docs: https://docs.github.com/en/actions
- YouTube API Docs: https://developers.google.com/youtube/v3
- Cron Time Converter: https://crontab.guru
- OAuth Guide: https://developers.google.com/identity/protocols/oauth2

---

**You're all set! Your YouTube shorts will upload automatically every day at 8:00 AM IST.** 🎉

Start by reading **QUICK_START.md** for the next steps.

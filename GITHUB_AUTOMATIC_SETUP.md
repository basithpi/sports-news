# Setup GitHub Automatic Daily Uploads (7 AM IST)

Your workflow is **ready to go**! Just add credentials and it will run automatically every day.

---

## 🎯 3 Steps to Activate Automatic Daily Uploads

### Step 1: Get Your Google OAuth JSON
If you haven't already:
1. Go to: https://console.cloud.google.com
2. Enable YouTube Data API v3
3. Create OAuth 2.0 Desktop Client
4. Download the JSON file
5. Open it and copy the entire content

---

### Step 2: Add GitHub Secret

⚠️ **IMPORTANT - This is the final step!**

1. Go to your repo: https://github.com/basithpi/sports-news/settings/secrets/actions
2. Click **"New repository secret"** button
3. Fill in:
   - **Name**: `GOOGLE_CLIENT_SECRET`
   - **Value**: Paste your entire Google OAuth JSON
4. Click **"Add secret"**

Done! ✓

---

### Step 3: Verify & Test

**Option A: Wait for automatic run**
- GitHub will automatically run at **7:00 AM IST daily**
- Check: Actions tab → "Daily YouTube Shorts Upload"

**Option B: Test immediately**
1. Go to: https://github.com/basithpi/sports-news/actions
2. Click: **"Daily YouTube Shorts Upload"** workflow
3. Click: **"Run workflow"** (yellow button)
4. Click: **"Run workflow"** again to confirm
5. Wait 2-3 minutes, then check logs

---

## 📅 What Happens Automatically

**Every day at 7:00 AM IST (01:30 UTC):**

1. ✅ GitHub Actions starts
2. ✅ Fetches sports news (football & cricket)
3. ✅ Generates 15 shorts
4. ✅ Uploads to your YouTube channel
5. ✅ Schedules publishes (15 min apart)
6. ✅ Saves OAuth token for next run
7. ✅ Deletes old output folders

**Total time:** ~15-20 minutes

---

## 🔍 Monitor Your Runs

### Check Status:
1. Go to: https://github.com/basithpi/sports-news/actions
2. Click "Daily YouTube Shorts Upload"
3. See all past runs with status (✓ passed / ✗ failed)

### View Logs:
1. Click on a run
2. Click "upload-shorts" job
3. Scroll to see all steps and output

### Download Generated Shorts:
1. Click on a successful run
2. Scroll to "Artifacts" section
3. Download `google-token` artifact (saves auth token)

---

## ⚠️ If Run Fails

**Common issues:**

### "Secret GOOGLE_CLIENT_SECRET not found"
→ You haven't added the secret yet. Follow Step 2 above.

### "Permission denied to YouTube"
→ First run needs authorization:
1. Run workflow manually (Step 3, Option B)
2. Check logs - it will ask to open browser
3. Authorize YouTube channel
4. Future runs will use saved token automatically

### "Quota exceeded"
→ You need more YouTube quota:
1. Go to Google Cloud Console → Quotas
2. Find "YouTube Data API v3"
3. Request increase to 50,000 units/day

### Workflow doesn't start at 7 AM
→ GitHub is UTC-based:
  - 7:00 AM IST = 01:30 UTC
  - Cron: `30 1 * * *` (already set)
  - May run 5-10 minutes late sometimes (GitHub scheduling)

---

## ✅ Complete Checklist

- [ ] Google OAuth JSON file downloaded
- [ ] Added `GOOGLE_CLIENT_SECRET` to GitHub Secrets
- [ ] Tested workflow manually (optional but recommended)
- [ ] Scheduled run confirmed for 7 AM IST daily
- [ ] First OAuth authorization completed

---

## 🎯 What You Have Now

| Feature | Status |
|---------|--------|
| Manual run on laptop | ✅ Working |
| YouTube upload | ✅ Working |
| GitHub automatic daily | ⏳ Ready (add secret to activate) |
| Time: 7:00 AM IST | ✅ Configured |
| Count: 15 shorts/day | ✅ Configured |

---

## 📞 Quick Commands

**Run manually on GitHub (test first run):**
1. Go to Actions tab
2. Click "Daily YouTube Shorts Upload"
3. Click "Run workflow"
4. Click "Run workflow" to confirm

**Run on your laptop anytime:**
```powershell
.\.venv\Scripts\Activate.ps1
python sports_shorts_pipeline.py --count 15
```

**Double-click to run:**
```
RUN_SHORTS.bat
```

---

## 🚀 That's It!

After you add the secret:
- ✅ Automatic daily at 7 AM IST
- ✅ 15 shorts uploaded
- ✅ No manual work needed
- ✅ Token auto-refreshes

**Action required:** Add `GOOGLE_CLIENT_SECRET` to GitHub Secrets (Step 2)

Then you're done! 🎉

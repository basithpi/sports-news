# GitHub Actions Automated Daily YouTube Shorts Upload

This guide sets up automatic daily uploads of 15 YouTube Shorts using GitHub Actions.

## Prerequisites

1. A GitHub repository (push this code to GitHub)
2. Google OAuth credentials for YouTube Data API
3. A YouTube channel to upload to

## Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**:
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to **Credentials** → **+ Create Credentials** → **OAuth client ID**
   - Select **Desktop application**
   - Download the JSON file
5. Copy the entire JSON content

## Step 2: Set Up GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add `GOOGLE_CLIENT_SECRET`:
   - **Name**: `GOOGLE_CLIENT_SECRET`
   - **Value**: Paste the entire JSON content from your credentials file

5. (Optional) Add `SCHEDULE_START_TIME`:
   - **Name**: `SCHEDULE_START_TIME`
   - **Value**: Your preferred first publish time (e.g., `2026-06-08T09:00:00+05:30`)
   - If not set, shorts will be scheduled starting 20 minutes after generation

## Step 3: Initial OAuth Authorization

The first run will need browser authorization:

1. Go to **Actions** tab in GitHub
2. Select **Daily YouTube Shorts Upload** workflow
3. Click **Run workflow** → **Run workflow**
4. Wait for the workflow to complete
5. The OAuth token will be saved automatically for future runs

## Step 4: Customize Schedule

The workflow runs daily at **8:00 AM IST** by default. To change:

1. Edit `.github/workflows/daily-shorts-upload.yml`
2. Modify the cron schedule line:
   ```yaml
   - cron: '30 2 * * *'  # 02:30 UTC = 8:00 AM IST
   ```
   
**Cron format**: `minute hour day month weekday`
- `30 2 * * *` = Every day at 02:30 UTC
- `0 8 * * *` = Every day at 08:00 UTC
- `0 9 * * 1-5` = Weekdays at 09:00 UTC

Use [crontab.guru](https://crontab.guru) to convert to your timezone.

## Step 5: Monitor Uploads

- Check the **Actions** tab to see workflow runs and logs
- Failed uploads will save logs as artifacts
- You can manually trigger uploads anytime via **Run workflow** button

## YouTube Upload Quota

⚠️ **Important**: YouTube Data API has quota limits. Each `videos.insert` request costs quota. 

Check your quota:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Quotas**
4. Search for "YouTube Data API v3"
5. Check "Videos insert" quota limit

**Default quota**: 10,000 units/day
- Each video upload = ~1,600 units
- 15 shorts/day ≈ 24,000 units (exceeds default quota)

**Solutions**:
1. **Request quota increase**: Go to quotas page → Select "YouTube Data API v3" → Click pencil → Request increase to 50,000+ units/day
2. **Upload fewer shorts**: Change `--count 15` to `--count 10` in the workflow
3. **Upload on alternate days**: Change cron to `30 2 * * 0,2,4` (Mon, Wed, Fri)

## Troubleshooting

### Workflow doesn't run automatically
- Check the workflow file syntax in **Actions** → **Daily YouTube Shorts Upload**
- Ensure your repository has Actions enabled

### OAuth token expired
- Delete the saved `google-token` artifact in Actions
- The next workflow run will request new authorization

### Insufficient quota
- Check quota usage in Google Cloud Console
- Request a quota increase (can take 24-48 hours)
- Temporarily reduce `--count` value

### Workflow stuck or timeout
- Artifacts are automatically deleted after 90 days to save storage
- You can manually cancel and retry from Actions tab

## Security Notes

✅ **What's secure:**
- Google credentials are only stored as GitHub Secrets (encrypted)
- OAuth token is stored as a GitHub artifact (private to your repository)
- Credentials are deleted after each workflow run

⚠️ **What to watch:**
- Don't commit `client_secret.json` to your repo (it's auto-deleted in workflow)
- Keep your GitHub repository private if storing sensitive info
- Regularly check OAuth token expiration (refresh happens automatically)

## Customization

### Upload fewer/more shorts daily
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
--count 15  # Change to 10, 20, etc.
```

### Change publish schedule
Edit `.github/workflows/daily-shorts-upload.yml`:
```yaml
--schedule-start "2026-06-08T09:00:00+05:30"  # Change time
--schedule-interval-minutes 15  # Change gap between publishes (min 20 recommended)
```

### Disable automatic upload (test mode)
Add `--no-upload-youtube` flag to disable actual YouTube uploads while testing.

## Next Steps

1. Push this code to GitHub
2. Add `GOOGLE_CLIENT_SECRET` to GitHub Secrets
3. Run workflow manually once for initial OAuth setup
4. Set up a quota increase if needed
5. Workflow will run automatically at scheduled time

#!/usr/bin/env pwsh
# Quick setup script for GitHub Actions daily uploads
# Run this after pushing to GitHub

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "GitHub Actions Daily Shorts Upload - Setup Checklist" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$steps = @(
    @{
        num = "1"
        title = "Create GitHub OAuth Credentials"
        items = @(
            "Visit: https://console.cloud.google.com",
            "Create new project (or select existing)",
            "Enable YouTube Data API v3",
            "Go to Credentials → Create OAuth 2.0 client (Desktop app)",
            "Download the JSON file"
        )
    },
    @{
        num = "2"
        title = "Push Code to GitHub"
        items = @(
            "git init",
            "git add .",
            "git commit -m 'Initial commit: Daily YouTube shorts pipeline'",
            "git branch -M main",
            "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO",
            "git push -u origin main"
        )
    },
    @{
        num = "3"
        title = "Add GitHub Secrets"
        items = @(
            "Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions",
            "Click 'New repository secret'",
            "Add GOOGLE_CLIENT_SECRET: (paste entire OAuth JSON content)",
            "(Optional) Add SCHEDULE_START_TIME: 2026-06-08T08:00:00+05:30"
        )
    },
    @{
        num = "4"
        title = "Request YouTube Quota Increase (IMPORTANT)"
        items = @(
            "15 shorts × 1600 units = 24,000 units/day (exceeds default 10,000)",
            "Visit: https://console.cloud.google.com/quotas",
            "Filter: YouTube Data API v3",
            "Click 'Videos: insert' quota",
            "Click pencil icon → Request quota increase to 50,000 units/day",
            "Approval usually takes 24-48 hours"
        )
    },
    @{
        num = "5"
        title = "Trigger First Run (for OAuth)"
        items = @(
            "Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions",
            "Select 'Daily YouTube Shorts Upload' workflow",
            "Click 'Run workflow' → 'Run workflow'",
            "Watch the log for any authorization prompts",
            "Token will be saved automatically for future runs"
        )
    },
    @{
        num = "6"
        title = "Verify Automation"
        items = @(
            "Check Actions tab for successful run",
            "Verify videos appeared on your YouTube channel",
            "Scheduled uploads will run automatically at 8:00 AM IST daily",
            "You can manually trigger uploads anytime via Actions → Run workflow"
        )
    }
)

foreach ($step in $steps) {
    Write-Host "📋 Step $($step.num): $($step.title)" -ForegroundColor Yellow
    Write-Host ""
    foreach ($item in $step.items) {
        Write-Host "   ✓ $item"
    }
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "⚠️  IMPORTANT NOTES:" -ForegroundColor Red
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. YouTube Quota:" -ForegroundColor White
Write-Host "   Default: 10,000 units/day"
Write-Host "   15 shorts/day: ~24,000 units"
Write-Host "   → MUST request quota increase or reduce daily count"
Write-Host ""
Write-Host "2. Schedule Time:" -ForegroundColor White
Write-Host "   Current: 8:00 AM IST (02:30 UTC) daily"
Write-Host "   Edit .github/workflows/daily-shorts-upload.yml to change"
Write-Host ""
Write-Host "3. First Authorization:" -ForegroundColor White
Write-Host "   First run needs browser auth (one-time)"
Write-Host "   Token saved automatically for future runs"
Write-Host ""
Write-Host "4. Credentials Security:" -ForegroundColor White
Write-Host "   ✓ Only stored as GitHub Secrets (encrypted)"
Write-Host "   ✓ Auto-deleted after each workflow run"
Write-Host "   ✓ Keep repository private"
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Need help? See GITHUB_SETUP.md for detailed troubleshooting" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

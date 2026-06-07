#!/usr/bin/env pwsh
# Quick start script for running shorts on your laptop

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  YouTube Shorts Generator - Local Setup                  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Activate virtual environment
Write-Host "Step 1: Activating Python environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "✓ Activated" -ForegroundColor Green
Write-Host ""

# Step 2: Show options
Write-Host "Step 2: Choose how many shorts to generate:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Option 1: Test mode (5 shorts, no upload)" -ForegroundColor Gray
Write-Host "    python sports_shorts_pipeline.py --count 5 --no-upload-youtube" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option 2: Generate & upload 10 shorts" -ForegroundColor Gray
Write-Host "    python sports_shorts_pipeline.py --count 10" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option 3: Generate & upload 15 shorts (RECOMMENDED)" -ForegroundColor Gray
Write-Host "    python sports_shorts_pipeline.py --count 15" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option 4: Custom (change 20 to desired count)" -ForegroundColor Gray
Write-Host "    python sports_shorts_pipeline.py --count 20" -ForegroundColor Cyan
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Ready to run! Copy and paste one of the commands above" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "ℹ️  First run will:" -ForegroundColor White
Write-Host "  • Ask for YouTube authorization in browser (one-time)" -ForegroundColor Gray
Write-Host "  • Generate shorts from sports news" -ForegroundColor Gray
Write-Host "  • Upload to your YouTube channel" -ForegroundColor Gray
Write-Host "  • Take 10-20 minutes total" -ForegroundColor Gray
Write-Host ""
Write-Host "📁 Output will be saved to: output\YYYYMMDD_HHMMSS\" -ForegroundColor White
Write-Host ""

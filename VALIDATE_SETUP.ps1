#!/usr/bin/env pwsh
# Validation script to check GitHub Actions setup

Write-Host ""
Write-Host "=" * 70
Write-Host "GitHub Actions Daily Shorts Upload - Validation Tool"
Write-Host "=" * 70
Write-Host ""

$issues = @()
$warnings = @()
$passes = @()

# Check 1: Required files exist
Write-Host "Checking file structure..." -ForegroundColor Yellow

@(
    ".github/workflows/daily-shorts-upload.yml"
    "sports_shorts_pipeline.py"
    "requirements.txt"
    "GITHUB_SETUP.md"
    "QUICK_START.md"
) | ForEach-Object {
    if (Test-Path $_) {
        $passes += "[OK] Found: $_"
    } else {
        $issues += "[ERROR] Missing: $_"
    }
}

# Check 2: Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($?) {
    $passes += "[OK] Python installed: $pythonVersion"
} else {
    $issues += "[ERROR] Python not found"
}

# Check 3: Git
Write-Host "Checking Git..." -ForegroundColor Yellow
$gitStatus = git status 2>&1
if ($?) {
    $passes += "[OK] Git repository initialized"
} else {
    $issues += "[ERROR] Not a git repository"
}

# Check 4: Files
Write-Host "Checking credentials..." -ForegroundColor Yellow
if (Test-Path "client_secret.json") {
    $warnings += "[WARN] client_secret.json should not be committed"
} else {
    $passes += "[OK] client_secret.json protected"
}

if (Test-Path ".gitignore") {
    $passes += "[OK] .gitignore found"
} else {
    $issues += "[ERROR] .gitignore missing"
}

# Display results
Write-Host ""
Write-Host "=" * 70
Write-Host "VALIDATION RESULTS"
Write-Host "=" * 70
Write-Host ""

if ($passes.Count -gt 0) {
    Write-Host "PASSED ($($passes.Count)):" -ForegroundColor Green
    $passes | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
}

if ($warnings.Count -gt 0) {
    Write-Host "WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
}

if ($issues.Count -gt 0) {
    Write-Host "ISSUES ($($issues.Count)):" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
}

$totalChecks = $passes.Count + $warnings.Count + $issues.Count
Write-Host "=" * 70
Write-Host "Ready to push: $(if ($issues.Count -eq 0) { 'YES' } else { 'NO' })"
Write-Host "=" * 70
Write-Host ""

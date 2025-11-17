# Cleanup Script for Trading Signal Analyzer
# Run this to clean up temporary files and caches

Write-Host "?? Cleaning Trading Signal Analyzer..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$cleanedItems = 0

# Python cache files
Write-Host "Cleaning Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "  ? Removed $($_.FullName)" -ForegroundColor Green
    $cleanedItems++
}

Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  ? Removed $($_.FullName)" -ForegroundColor Green
    $cleanedItems++
}

# Node modules cache
if (Test-Path "frontend\node_modules\.cache") {
    Write-Host "Cleaning Node cache..." -ForegroundColor Yellow
    Remove-Item "frontend\node_modules\.cache" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ? Removed node_modules/.cache" -ForegroundColor Green
    $cleanedItems++
}

# React build cache
if (Test-Path "frontend\.cache") {
    Remove-Item "frontend\.cache" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ? Removed frontend/.cache" -ForegroundColor Green
    $cleanedItems++
}

# ESLint cache
if (Test-Path "frontend\.eslintcache") {
    Remove-Item "frontend\.eslintcache" -Force -ErrorAction SilentlyContinue
    Write-Host "  ? Removed .eslintcache" -ForegroundColor Green
    $cleanedItems++
}

# Log files (optional - comment out if you want to keep logs)
Write-Host "Cleaning old logs..." -ForegroundColor Yellow
Get-ChildItem -Path "backend\logs" -Filter "*.log*" -File -ErrorAction SilentlyContinue | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-7)
} | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  ? Removed old log: $($_.Name)" -ForegroundColor Green
    $cleanedItems++
}

# Cached data older than 24 hours
Write-Host "Cleaning old cache data..." -ForegroundColor Yellow
if (Test-Path "backend\data\cache") {
    Get-ChildItem -Path "backend\data\cache" -File -ErrorAction SilentlyContinue | Where-Object {
        $_.LastWriteTime -lt (Get-Date).AddHours(-24)
    } | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "  ? Removed cached file: $($_.Name)" -ForegroundColor Green
        $cleanedItems++
    }
}

# Old Excel reports
Write-Host "Cleaning old reports..." -ForegroundColor Yellow
if (Test-Path "backend\data\reports") {
    Get-ChildItem -Path "backend\data\reports" -Filter "*.xlsx" -File -ErrorAction SilentlyContinue | Where-Object {
        $_.LastWriteTime -lt (Get-Date).AddDays(-7)
    } | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "  ? Removed old report: $($_.Name)" -ForegroundColor Green
        $cleanedItems++
    }
}

# OS-specific files
Write-Host "Cleaning OS-specific files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "Thumbs.db" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  ? Removed $($_.FullName)" -ForegroundColor Green
    $cleanedItems++
}

Get-ChildItem -Path . -Filter ".DS_Store" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  ? Removed $($_.FullName)" -ForegroundColor Green
    $cleanedItems++
}

Get-ChildItem -Path . -Filter "desktop.ini" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  ? Removed $($_.FullName)" -ForegroundColor Green
    $cleanedItems++
}

Write-Host ""
Write-Host "? Cleanup complete!" -ForegroundColor Green
Write-Host "Removed $cleanedItems items" -ForegroundColor Cyan
Write-Host ""

# Optional: Show disk space saved (rough estimate)
Write-Host "?? Tip: To deep clean, you can also:" -ForegroundColor Yellow
Write-Host "  - Remove node_modules: rm -r frontend\node_modules" -ForegroundColor White
Write-Host "  - Remove venv: rm -r backend\venv" -ForegroundColor White
Write-Host "  - Then run .\setup.ps1 to reinstall" -ForegroundColor White
Write-Host ""

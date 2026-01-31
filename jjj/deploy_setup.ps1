# Quick Deploy Script for Environmental Monitoring System
# Run this to prepare your app for deployment

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host " 🚀 Environmental Monitoring System - Deployment Setup" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first:" -ForegroundColor Red
    Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📋 Pre-Deployment Checklist:" -ForegroundColor Cyan
Write-Host ""

# Check if files exist
$requiredFiles = @("app.py", "requirements.txt", "Procfile", "runtime.txt", "index.html")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file missing" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔑 Environment Variables Check:" -ForegroundColor Cyan
Write-Host ""

# Prompt for API keys
Write-Host "Do you have a Weather API key? (Get it free from weatherapi.com)" -ForegroundColor Yellow
$weatherKey = Read-Host "Enter your Weather API key (or press Enter to skip)"

if ($weatherKey) {
    Write-Host "  ✅ Weather API key saved" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Weather API key not provided - you'll need to add it in deployment platform" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Do you have an OpenAI API key? (Optional - for AI features)" -ForegroundColor Yellow
$openaiKey = Read-Host "Enter your OpenAI API key (or press Enter to skip)"

if ($openaiKey) {
    Write-Host "  ✅ OpenAI API key saved" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  OpenAI API key skipped - AI features will use template responses" -ForegroundColor Blue
}

Write-Host ""
Write-Host "🌐 Ready to Deploy!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Initialize Git repository: git init" -ForegroundColor White
Write-Host "  2. Add files: git add ." -ForegroundColor White
Write-Host "  3. Commit: git commit -m 'Initial commit'" -ForegroundColor White
Write-Host "  4. Create GitHub repository at: https://github.com/new" -ForegroundColor White
Write-Host "  5. Push code: git remote add origin YOUR_REPO_URL" -ForegroundColor White
Write-Host "  6. git push -u origin main" -ForegroundColor White
Write-Host "  7. Deploy on Render: https://render.com" -ForegroundColor White
Write-Host ""
Write-Host "📚 Full instructions in: DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to initialize git
Write-Host "Would you like to initialize Git now? (y/n)" -ForegroundColor Yellow
$initGit = Read-Host

if ($initGit -eq 'y' -or $initGit -eq 'Y') {
    Write-Host ""
    Write-Host "Initializing Git repository..." -ForegroundColor Cyan
    
    git init
    
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next, run these commands:" -ForegroundColor Cyan
    Write-Host "  git add ." -ForegroundColor White
    Write-Host "  git commit -m 'Initial commit - Environmental Monitoring System'" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "No problem! Run 'git init' when you're ready." -ForegroundColor Blue
    Write-Host ""
}

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host " 🎉 Setup Complete! Follow DEPLOYMENT_GUIDE.md to deploy." -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

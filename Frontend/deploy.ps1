# Frontend Firebase Hosting Deployment Script (PowerShell)

Write-Host "Deploying MedAssure AI Frontend to Firebase Hosting..." -ForegroundColor Green

# Configuration
$PROJECT_ID = "gen-lang-client-0182599221"

# Set the Firebase project
Write-Host "Setting Firebase project..." -ForegroundColor Yellow
firebase use $PROJECT_ID

# Install dependencies if node_modules doesn't exist or package-lock.json is newer
if (!(Test-Path "node_modules") -or (Get-Item "package-lock.json").LastWriteTime -gt (Get-Item "node_modules").LastWriteTime) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Build the React application for production
Write-Host "Building React application for production..." -ForegroundColor Yellow
npm run build

# Check if build was successful
if (!(Test-Path "build")) {
    Write-Host "Build failed - build directory not found!" -ForegroundColor Red
    exit 1
}

# Deploy to Firebase Hosting
Write-Host "Deploying to Firebase Hosting..." -ForegroundColor Yellow
firebase deploy --only hosting

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Your app is now live at: https://$PROJECT_ID.web.app" -ForegroundColor Cyan
Write-Host "Alternative URL: https://$PROJECT_ID.firebaseapp.com" -ForegroundColor Cyan


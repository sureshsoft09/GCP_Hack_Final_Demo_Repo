# Frontend Firebase Hosting Deployment Guide

This guide covers deploying the MedAssure AI Frontend to Firebase Hosting.

## Prerequisites

1. **Node.js and npm**: Ensure Node.js (v16+) and npm are installed
2. **Firebase CLI**: Install with `npm install -g firebase-tools`
3. **Firebase Authentication**: Login with `firebase login`
4. **Backend Deployed**: Ensure the backend is deployed to Cloud Run first

## Project Setup

The project is already configured for Firebase Hosting with:
- **Project ID**: `gen-lang-client-0182599221`
- **Build Directory**: `build` (React production build)
- **SPA Configuration**: Rewrites all routes to `/index.html`

## Environment Configuration

### Production Environment (`.env.production`)
```bash
REACT_APP_API_BASE_URL=https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app
GENERATE_SOURCEMAP=false
```

### Local Development (`.env.local`)
```bash
# Using production backend
REACT_APP_API_BASE_URL=https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app

# OR for local backend development:
# REACT_APP_API_BASE_URL=http://localhost:8083
```

## Deployment Options

### Option 1: PowerShell Script (Windows)
```powershell
./deploy.ps1
```

### Option 2: Bash Script (Linux/Mac)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 3: Manual Deployment

**Step 1: Install Dependencies**
```bash
npm install
```

**Step 2: Build the Application**
```bash
npm run build
```
*This creates the production build in the `build/` directory*

**Step 3: Deploy to Firebase**
```bash
firebase deploy --only hosting
```

**Important**: Always run `npm run build` before deployment to ensure the latest code changes are included.
# Set Firebase project
firebase use gen-lang-client-0182599221

# Install dependencies
npm install

# Build for production
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

## Build Process

The deployment script will:
1. Set the Firebase project to `gen-lang-client-0182599221`
2. Install npm dependencies (if needed)
3. Build the React app for production
4. Deploy the `build` folder to Firebase Hosting

## Firebase Configuration

### `firebase.json`
```json
{
  "hosting": {
    "public": "build",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{"source": "**", "destination": "/index.html"}],
    "headers": [/* Caching headers for static assets */]
  }
}
```

### `.firebaserc`
```json
{
  "projects": {
    "default": "gen-lang-client-0182599221"
  }
}
```

## Deployment URLs

After successful deployment, your app will be available at:
- **Primary URL**: https://gen-lang-client-0182599221.web.app
- **Alternative URL**: https://gen-lang-client-0182599221.firebaseapp.com

## Environment Variables

The frontend uses the following environment variables:

### Build-time Variables
- `REACT_APP_API_BASE_URL`: Backend API endpoint URL
- `GENERATE_SOURCEMAP`: Controls source map generation (false for production)

### API Configuration
The frontend is configured to connect to:
```
Backend: https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app
```

## Testing the Deployment

After deployment, test the application:

1. **Open the app**: Visit https://gen-lang-client-0182599221.web.app
2. **Check console**: Open browser dev tools, verify no API errors
3. **Test features**: Upload files, generate content, navigate pages
4. **API connectivity**: Verify frontend connects to Cloud Run backend

## Firebase Hosting Features

### Caching Strategy
- **Static assets** (JS, CSS, images): 1 year cache
- **HTML files**: No cache (always fresh)
- **API calls**: Handled by backend, no frontend caching

### Single Page Application (SPA)
- All routes redirect to `/index.html`
- Client-side routing handled by React Router
- 404 handling managed by React application

### HTTPS & CDN
- Automatic HTTPS certificate
- Global CDN for fast loading
- Gzip compression enabled

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check Node.js version
   node --version  # Should be 16+
   
   # Clear node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **API Connection Issues**
   ```bash
   # Verify backend is deployed and accessible
   curl https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app/health
   
   # Check environment variables
   cat .env.production
   ```

3. **Firebase CLI Issues**
   ```bash
   # Update Firebase CLI
   npm install -g firebase-tools@latest
   
   # Re-authenticate
   firebase logout
   firebase login
   ```

4. **Deployment Permission Issues**
   ```bash
   # Check project access
   firebase projects:list
   
   # Ensure you have Editor/Owner role on the project
   ```

### Debug Mode

For debugging, you can build with source maps:
```bash
# Temporarily enable source maps
echo "GENERATE_SOURCEMAP=true" > .env.local
npm run build
firebase deploy --only hosting
```

## Custom Domain (Optional)

To set up a custom domain:
```bash
# Add custom domain
firebase hosting:sites:create your-domain.com

# Configure DNS records as instructed
# Deploy to custom domain
firebase target:apply hosting production your-domain.com
firebase deploy --only hosting:production
```

## Monitoring & Analytics

### Firebase Hosting Metrics
```bash
# View hosting analytics
firebase hosting:clone:list

# Check deployment history
firebase hosting:sites:get gen-lang-client-0182599221
```

### Performance Monitoring
Consider adding Firebase Performance Monitoring:
```bash
npm install firebase
# Add performance monitoring code to src/index.js
```

## Production Considerations

1. **Security**: Verify CORS settings in backend allow the Firebase domain
2. **Performance**: Monitor Core Web Vitals in Firebase console
3. **Analytics**: Consider adding Google Analytics or Firebase Analytics
4. **Monitoring**: Set up uptime monitoring for the application
5. **Backup**: Ensure you have access to source code and can redeploy

## Integration

### Backend Integration
The frontend is configured to connect to:
- **Backend Service**: medassure-backend (Cloud Run)
- **Authentication**: Handled by backend service account
- **CORS**: Backend configured to allow Firebase Hosting domain

### API Endpoints Used
- `GET /health` - Health check
- `POST /generate` - Content generation
- `POST /review` - Requirements review
- `POST /upload` - File upload and processing
- `GET /projects` - Project listing
- `GET /projects/{id}` - Project details

## Rollback Process

If you need to rollback to a previous version:
```bash
# List previous releases
firebase hosting:releases:list

# Rollback to specific release
firebase hosting:releases:rollback RELEASE_ID
```

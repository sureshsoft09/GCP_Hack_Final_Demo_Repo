# Backend Cloud Run Deployment Script (PowerShell)

# Configuration
$GOOGLE_CLOUD_PROJECT = "gen-lang-client-0182599221"
$REGION = "europe-west1"
$SERVICE_NAME = "medassureai-backend-server"
$SERVICE_ACCOUNT = "medassureaibackendfrontendsca@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com"

# Ensure you're authenticated and project is set
Write-Host "Setting up Google Cloud configuration..." -ForegroundColor Green
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage.googleapis.com

# Grant necessary permissions to the service account
Write-Host "Granting permissions to existing service account..." -ForegroundColor Green
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/logging.logWriter"

# Deploy to Cloud Run using source deployment
Write-Host "Deploying Backend to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --service-account=$SERVICE_ACCOUNT `
    --allow-unauthenticated `
    --region=$REGION `
    --source=. `
    --labels=dev-medassai=backend-service `
    --memory=1Gi `
    --cpu=1 `
    --max-instances=10 `
    --min-instances=1 `
    --timeout=1200 `
    --concurrency=80 `
    --set-env-vars="AGENTS_API_URL=https://agents-server-145534422719.europe-west1.run.app/query" `
    --set-env-vars="RESET_AGENT_SESSION_API_URL=https://agents-server-145534422719.europe-west1.run.app/reset-session" `
    --set-env-vars="AGENTS_API_TIMEOUT=1200" `
    --set-env-vars="GOOGLE_CLOUD_BUCKET=medassure-ai-documents1" `
    --set-env-vars="FIRESTORE_PROJECT_ID=gen-lang-client-0182599221" `
    --set-env-vars="FIRESTORE_DATABASE_NAME=medassureaifirestoredb" `
    --set-env-vars="FIRESTORE_PROJECTS_COLLECTION=testcase_projects" `
    --set-env-vars="MAX_FILE_SIZE=50485760" `
    --set-env-vars="MAX_TEXT_LENGTH=1048576" `
    --set-env-vars="ENVIRONMENT=production" `
    --set-env-vars="DEBUG=false" `
    --project=$GOOGLE_CLOUD_PROJECT


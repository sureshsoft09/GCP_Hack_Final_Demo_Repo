# JIRA MCP Server Cloud Run Deployment Script (PowerShell)

# Configuration
$GOOGLE_CLOUD_PROJECT = "gen-lang-client-0182599221"  # Replace with your GCP project ID
$REGION = "europe-west1"                       # Using europe-west1 as specified
$SERVICE_NAME = "jira-mcp-server"
$SERVICE_ACCOUNT = "firestoreconnectserviceacc@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com"

# Ensure you're authenticated and project is set
Write-Host "Setting up Google Cloud configuration..." -ForegroundColor Green
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com


# Deploy to Cloud Run using source deployment
Write-Host "Deploying JIRA MCP Server to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --service-account=$SERVICE_ACCOUNT `
    --no-allow-unauthenticated `
    --region=$REGION `
    --source=. `
    --labels=dev-medassai=jira-mcp `
    --memory=512Mi `
    --cpu=1 `
    --max-instances=10 `
    --min-instances=0 `
    --timeout=600 `
    --concurrency=80 `
    --set-env-vars="JIRA_BASE_URL=https://hsskill.atlassian.net,JIRA_EMAIL=aravinthan.babu@gmail.com,JIRA_API_TOKEN=ATATT3xFfGF0qICQDCOkIooiOpkMakbkfgc12T_qeE7waGnsYer5POSma97gpiwnX6QAi8nvm9-h7bqDupLQog59fib5gsrokfNA-6S4L5gQxva2Eh_YaW6g-KOHhHgqp5ryqzu9W5mnvWAubIFE7LGJ77emj4l8O0-FqEL8GBUOkwOdKji5TIc=B5713370,JIRA_PROJECT_KEY=HS25SKL" `
    --project=$GOOGLE_CLOUD_PROJECT

Write-Host "Deployment completed!" -ForegroundColor Green

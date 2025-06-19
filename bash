# Authenticate and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable necessary services
gcloud services enable run containerregistry sqladmin

# Build Docker image and push to Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/zkill-listener

# Deploy to Cloud Run
gcloud run deploy zkill-listener \
  --image gcr.io/YOUR_PROJECT_ID/zkill-listener \
  --platform managed \
  --region us-central1 \
  --set-env-vars DB_HOST='...',DB_PORT='5432',DB_NAME='...',DB_USER='...',DB_PASSWORD='...',WATCHED_CORP_IDS='123456,234567' \
  --allow-unauthenticated

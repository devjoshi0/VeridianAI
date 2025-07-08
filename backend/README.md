# AI Newsletter Backend

This backend handles news fetching, AI summarization, and personalized newsletter generation.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the backend directory with the following variables:

```env
# Firebase Service Account Key (JSON string)
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project-id","private_key_id":"your-private-key-id","private_key":"-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"your-client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com","universe_domain":"googleapis.com"}

# TheNewsAPI Token
THENEWS_API_TOKEN=your_news_api_token_here
```

### 3. Get Firebase Service Account Key
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Project Settings → Service Accounts
4. Click "Generate new private key"
5. Download the JSON file
6. Copy the entire JSON content and paste it as the value for `FIREBASE_SERVICE_ACCOUNT_KEY`

### 4. Get TheNewsAPI Token
1. Sign up at [TheNewsAPI](https://thenewsapi.com/)
2. Get your API token from the dashboard
3. Add it as the value for `THENEWS_API_TOKEN`

## Usage

### Test Firebase Connection
```bash
python test_firebase_connection.py
```

### Run Individual Components
```bash
# Fetch news articles
python fetch_news.py

# Summarize articles
python summarize_articles.py

# Run full pipeline
python ai_pipeline.py
```

## Security Notes

- Never commit the `.env` file to version control
- The `.gitignore` file is configured to exclude sensitive files
- All API keys and service account credentials are stored in environment variables
- The service account key file has been removed from the repository

## Data Flow

1. **fetch_news.py** - Fetches articles from TheNewsAPI and stores in Firestore `raw_articles` collection
2. **summarize_articles.py** - Reads articles from Firestore, summarizes them using BART model, and stores in `summaries` collection
3. **ai_pipeline.py** - Orchestrates the entire process and creates personalized newsletters in `newsletters` collection 
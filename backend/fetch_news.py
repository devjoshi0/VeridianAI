import http.client
import urllib.parse
import json
from datetime import datetime, UTC
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase
try:
    # Try to initialize with service account key from environment variable
    service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    if service_account_key:
        import json
        cred_dict = json.loads(service_account_key)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized with environment variable")
    else:
        # Fallback to default credentials (for local development)
        firebase_admin.initialize_app()
        print("Firebase initialized with default credentials")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    print("Please set FIREBASE_SERVICE_ACCOUNT_KEY in your .env file")
    exit(1)

db = firestore.client()

API_TOKEN = os.getenv('THENEWS_API_TOKEN')
if not API_TOKEN:
    print("THENEWS_API_TOKEN not found in environment variables")
    exit(1)
topics = ['general', 'science', 'sports', 'tech', 'entertainment']  # Add more as needed

today = datetime.now(UTC).date()

for topic in topics:
    print(f"Fetching news for topic: {topic}")
    
    conn = http.client.HTTPSConnection('api.thenewsapi.com')
    params = urllib.parse.urlencode({
        'api_token': API_TOKEN,
        'categories': topic,
        'language': 'en',
        'limit': 50,  # Get as many as allowed, will filter for today below
    })
    conn.request('GET', f'/v1/news/all?{params}')
    res = conn.getresponse()
    data = res.read()
    articles = json.loads(data.decode('utf-8')).get('data', [])

    articles_today = []
    for article in articles:
        published_at = article.get("published_at")
        if published_at:
            article_date = datetime.fromisoformat(published_at.replace("Z", "+00:00")).date()
            if article_date == today:
                articles_today.append(article)
        if len(articles_today) == 3:
            break  # Only keep up to 3 articles

    # Save to Firestore instead of local file
    if articles_today:
        try:
            doc_ref = db.collection('raw_articles').document(f"{topic}_{today}")
            doc_ref.set({
                'topic': topic,
                'date': today.isoformat(),
                'articles': articles_today,
                'count': len(articles_today),
                'fetched_at': firestore.SERVER_TIMESTAMP
            })
            print(f"Saved {len(articles_today)} articles for {topic} to Firestore")
        except Exception as e:
            print(f"Failed to save articles for {topic}: {e}")
    else:
        print(f"No articles found for {topic} today")

print(f"\nNews fetching completed for {len(topics)} topics")

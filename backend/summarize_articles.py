import json
import os
from datetime import datetime, UTC
from newspaper import Article
from transformers import pipeline
import firebase_admin
from firebase_admin import credentials, firestore
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

# Set up summarizer
print("Loading BART summarization model...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
print("Summarization model loaded")

topics = ['general', 'science', 'sports', 'tech', 'entertainment']
today = datetime.now(UTC).date()

for topic in topics:
    print(f"\nProcessing summaries for topic: {topic}")
    
    try:
        # Get articles from Firestore
        doc_ref = db.collection('raw_articles').document(f"{topic}_{today}")
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"No articles found for {topic} today")
            continue
            
        data = doc.to_dict()
        articles = data.get('articles', [])
        
        if not articles:
            print(f"No articles in document for {topic}")
            continue
            
    except Exception as e:
        print(f"Failed to get articles for {topic}: {e}")
        continue

    summaries = []
    for i, article in enumerate(articles):
        url = article.get("url")
        if not url:
            continue

        print(f"  Processing article {i+1}/{len(articles)}: {url[:50]}...")

        # Scrape the article text
        try:
            news_article = Article(url)
            news_article.download()
            news_article.parse()
            text = news_article.text
        except Exception as e:
            print(f"    Failed to extract article: {e}")
            continue

        if not text or len(text.split()) < 50:
            print(f"    Article too short or empty")
            continue

        # Summarize the article
        try:
            summary = summarizer(text, max_length=1000, min_length=50, do_sample=False)[0]['summary_text']
        except Exception as e: 
            print(f"    Summarization failed: {e}")
            continue

        # Use the title as the catchy header
        header = article.get("title", "No Title")

        summaries.append({
            "header": header,
            "summary": summary,
            "url": url,
            "original_article": article  # Keep reference to original
        })
        
        print(f"    Summarized successfully")

    # Save summaries to Firestore
    if summaries:
        try:
            doc_ref = db.collection('summaries').document(f"{topic}_{today}")
            doc_ref.set({
                'topic': topic,
                'date': today.isoformat(),
                'summaries': summaries,
                'count': len(summaries),
                'created_at': firestore.SERVER_TIMESTAMP
            })
            print(f"Saved {len(summaries)} summaries for {topic} to Firestore")
        except Exception as e:
            print(f"Failed to save summaries for {topic}: {e}")
    else:
        print(f"No summaries created for {topic}")

print(f"\nSummarization completed for {len(topics)} topics")

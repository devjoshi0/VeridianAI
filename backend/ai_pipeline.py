import os
import json
import sys
from datetime import datetime, UTC
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import http.client
import urllib.parse
from newspaper import Article
from transformers import pipeline

# Load environment variables
load_dotenv()

# --- Firebase Initialization ---
try:
    service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    if service_account_key:
        cred_dict = json.loads(service_account_key)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized with environment variable")
    else:
        firebase_admin.initialize_app()
        print("Firebase initialized with default credentials")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    print("Please set FIREBASE_SERVICE_ACCOUNT_KEY in your .env file")
    sys.exit(1)

db = firestore.client()

# --- Summarization Model Initialization ---
print("Loading summarization model...")
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    print("Summarization model loaded successfully.")
except Exception as e:
    print(f"Failed to load summarization model: {e}")
    sys.exit(1)

# --- News Fetching ---
def fetch_articles_for_topic(topic: str, api_token: str) -> List[Dict[str, Any]]:
    """Fetches news articles for a given topic from the API."""
    print(f"Fetching news for topic: {topic}")
    today = datetime.now(UTC).date()
    
    conn = http.client.HTTPSConnection('api.thenewsapi.com')
    params = urllib.parse.urlencode({
        'api_token': api_token,
        'categories': topic,
        'language': 'en',
        'limit': 10,  # Fetch a few articles
    })
    
    try:
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
        
        print(f"Found {len(articles_today)} articles for {topic} today.")
        return articles_today
    except Exception as e:
        print(f"Failed to fetch articles for {topic}: {e}")
        return []
    finally:
        conn.close()

# --- Article Summarization ---
def summarize_article(article_data: Dict[str, Any]) -> Dict[str, Any] | None:
    """Summarizes a single article."""
    url = article_data.get("url")
    if not url:
        return None

    print(f"  Processing article: {url[:70]}...")
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        
        if not text or len(text.split()) < 100:
            print("    Article too short to summarize.")
            return None
            
        summary = summarizer(text, max_length=150, min_length=40, do_sample=False)[0]['summary_text']
        
        return {
            "header": article.title or article_data.get("title", "No Title"),
            "summary": summary,
            "url": url,
            "image": article.top_image or article_data.get("image_url"),
            "original_article": article_data
        }
    except Exception as e:
        print(f"    Failed to process article {url}: {e}")
        return None

# --- Firestore Operations ---
def store_summaries(topic: str, summaries: List[Dict[str, Any]]) -> None:
    """Stores summaries for a topic in Firestore."""
    if not summaries:
        print(f"No summaries to store for {topic}")
        return
        
    today = datetime.now(UTC).date()
    try:
        doc_ref = db.collection('summaries').document(f"{topic}_{today.isoformat()}")
        doc_ref.set({
            'topic': topic,
            'date': today.isoformat(),
            'summaries': summaries,
            'count': len(summaries),
            'created_at': firestore.SERVER_TIMESTAMP
        })
        print(f"Stored {len(summaries)} summaries for {topic} in Firestore.")
    except Exception as e:
        print(f"Failed to store summaries for {topic}: {e}")

def get_user_preferences() -> Dict[str, List[str]]:
    """Gets all users and their topic preferences from Firestore."""
    try:
        users_ref = db.collection('users')
        users = users_ref.stream()
        
        user_preferences = {}
        for user in users:
            user_data = user.to_dict()
            topics = user_data.get('topics', [])
            if topics:
                user_preferences[user.id] = topics
        
        print(f"Retrieved preferences for {len(user_preferences)} users.")
        return user_preferences
    except Exception as e:
        print(f"Failed to get user preferences: {e}")
        return {}

def create_personalized_newsletter(user_id: str, topics: List[str]) -> Dict[str, Any]:
    """Creates a personalized newsletter for a specific user."""
    today = datetime.now(UTC).date()
    newsletter_content = {
        'user_id': user_id,
        'date': today.isoformat(),
        'sections': [],
        'total_articles': 0
    }
    
    for topic in topics:
        try:
            doc_ref = db.collection('summaries').document(f"{topic}_{today.isoformat()}")
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                summaries = data.get('summaries', [])
                
                if summaries:
                    newsletter_content['sections'].append({
                        'topic': topic,
                        'articles': summaries
                    })
                    newsletter_content['total_articles'] += len(summaries)
        except Exception as e:
            print(f"Failed to get summaries for topic {topic}: {e}")
    
    return newsletter_content

def store_newsletters_in_firestore(newsletters: Dict[str, Dict[str, Any]]) -> None:
    """Stores personalized newsletters in Firestore."""
    today = datetime.now(UTC).date()
    
    for user_id, newsletter in newsletters.items():
        try:
            doc_ref = db.collection('newsletters').document(f"{user_id}_{today.isoformat()}")
            doc_ref.set({
                'user_id': user_id,
                'date': today.isoformat(),
                'content': newsletter,
                'created_at': firestore.SERVER_TIMESTAMP,
                'delivered': False
            })
            print(f"Stored newsletter for user {user_id} with {newsletter['total_articles']} articles.")
        except Exception as e:
            print(f"Failed to store newsletter for user {user_id}: {e}")

# --- Main Pipeline Orchestrator ---
def main():
    """Main AI pipeline orchestrator."""
    print("Starting AI Newsletter Pipeline")
    print("=" * 50)
    
    api_token = os.getenv('THENEWS_API_TOKEN')
    if not api_token:
        print("THENEWS_API_TOKEN not found in environment variables. Cannot fetch news.")
        return

    topics = ['general', 'science', 'sports', 'tech', 'entertainment']
    
    # Step 1 & 2: Fetch and Summarize Articles for each topic
    print("\nStep 1 & 2: Fetching and Summarizing Articles...")
    for topic in topics:
        articles = fetch_articles_for_topic(topic, api_token)
        summaries = []
        if articles:
            for article_data in articles:
                summary = summarize_article(article_data)
                if summary:
                    summaries.append(summary)
        store_summaries(topic, summaries)

    # Step 3: Get user preferences
    print("\nStep 3: Getting user preferences...")
    user_preferences = get_user_preferences()
    
    if not user_preferences:
        print("No users with preferences found. Exiting.")
        return
    
    # Step 4: Create personalized newsletters
    print("\nStep 4: Creating personalized newsletters...")
    newsletters = {}
    for user_id, user_topics in user_preferences.items():
        newsletter = create_personalized_newsletter(user_id, user_topics)
        if newsletter['total_articles'] > 0:
            newsletters[user_id] = newsletter
    
    # Step 5: Store newsletters in Firestore
    print("\nStep 5: Storing newsletters in Firestore...")
    if newsletters:
        store_newsletters_in_firestore(newsletters)
    else:
        print("No newsletters were created.")
    
    print("\nAI Pipeline completed successfully!")
    print(f"Summary: Created {len(newsletters)} personalized newsletters.")

if __name__ == "__main__":
    main()

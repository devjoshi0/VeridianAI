import os
import json
import sys
import requests
from datetime import datetime, UTC
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import http.client
import urllib.parse
from newspaper import Article
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

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

# --- Sentence Similarity Model Initialization ---
print("Loading sentence similarity model...")
try:
    similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Sentence similarity model loaded successfully.")
except Exception as e:
    print(f"Failed to load sentence similarity model: {e}")
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
        'limit': 5,  # Fetch a few articles
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

# --- Duplicate Detection ---
processed_articles_embeddings = {}

def is_duplicate(topic: str, article_text: str, threshold: float = 0.95) -> bool:
    """
    Checks if an article is a duplicate of one already processed for the same topic today.
    """
    if not article_text:
        return False

    # Reset cache for a new day's run if topic date changes (conceptual)
    # For this script, it resets per run. A more robust solution might use Redis or a DB.
    if topic not in processed_articles_embeddings:
        processed_articles_embeddings[topic] = []

    new_article_embedding = similarity_model.encode(article_text, convert_to_tensor=True)

    for existing_embedding in processed_articles_embeddings[topic]:
        similarity = util.pytorch_cos_sim(new_article_embedding, existing_embedding)
        if similarity.item() > threshold:
            print(f"    Duplicate article detected for topic {topic} with similarity {similarity.item():.4f}.")
            return True

    processed_articles_embeddings[topic].append(new_article_embedding)
    return False

# --- Article Summarization ---
def summarize_article(article_data: Dict[str, Any], topic: str) -> Dict[str, Any] | None:
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

        if is_duplicate(topic, text):
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

def create_personalized_newsletter(user_id: str, user_topics: List[str]) -> Dict[str, Any]:
    """Creates a personalized newsletter for a specific user, including only their selected topics."""
    today = datetime.now(UTC).date()
    newsletter_content = {
        'user_id': user_id,
        'date': today.isoformat(),
        'sections': [],
        'total_articles': 0
    }
    for topic in user_topics:  # Only loop over the user's selected topics
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

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_FROM_EMAIL = os.getenv('MAILGUN_FROM_EMAIL')

def send_newsletter_mailgun(to_email, subject, html_content):
    if not (MAILGUN_API_KEY and MAILGUN_DOMAIN and MAILGUN_FROM_EMAIL):
        print("Mailgun environment variables not set.")
        return False
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": MAILGUN_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
    )
    return response

def render_newsletter_html(newsletter):
    # Only topics in newsletter['sections'] (i.e., user-selected topics) are rendered below
    # Emoji/icon mapping for topics (customize as needed)
    topic_icons = {
        'science': '🔬',
        'sports': '🏅',
        'tech': '💻',
        'entertainment': '🎬',
        'general': '📰',
    }
    # Inline CSS for email compatibility
    style = '''
    <style>
      body { font-family: Arial, sans-serif; background: #181a1b; color: #fff; margin: 0; padding: 0; }
      .newsletter-container { max-width: 600px; margin: 0 auto; background: #23272a; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px #0003; }
      .header { background: #181a1b; padding: 24px 24px 8px 24px; text-align: center; }
      .header .date { color: #aaa; font-size: 14px; margin-bottom: 8px; }
      .header h1 { margin: 0 0 8px 0; font-size: 28px; color: #fff; }
      .greeting { font-size: 16px; color: #eee; margin-bottom: 16px; }
      .toc { background: #23272a; padding: 16px 24px; border-bottom: 1px solid #333; }
      .toc h2 { font-size: 18px; color: #fff; margin: 0 0 8px 0; }
      .toc ul { padding-left: 20px; margin: 0; }
      .toc li { font-size: 15px; margin-bottom: 4px; color: #fff; }
      .main { padding: 24px; }
      .article { margin-bottom: 32px; }
      .article h3 { margin: 0 0 8px 0; font-size: 20px; color: #fff; }
      .article a { color: #4ea1f7; text-decoration: none; }
      .article ul { margin: 0 0 0 20px; color: #eee; }
      .footer { background: #181a1b; color: #aaa; text-align: center; font-size: 13px; padding: 16px 24px; border-top: 1px solid #333; }
      .footer a { color: #4ea1f7; text-decoration: underline; }
      .social-icons img { width: 24px; height: 24px; margin: 0 4px; vertical-align: middle; }
    </style>
    '''
    # Date header
    from datetime import datetime
    date_str = datetime.strptime(newsletter['date'], '%Y-%m-%d').strftime('%A %d %B %Y')
    # Table of contents (headlines)
    toc_items = []
    article_anchors = []
    anchor_count = 1
    for section in newsletter['sections']:
        icon = topic_icons.get(section['topic'], '📰')
        for article in section['articles']:
            anchor = f"article{anchor_count}"
            toc_items.append(f'<li>{icon} <a href="#{anchor}" style="color:#4ea1f7;text-decoration:none;">{article["header"]}</a></li>')
            article_anchors.append((anchor, icon, article))
            anchor_count += 1
    # Main content
    main_html = ""
    for anchor, icon, article in article_anchors:
        main_html += f'''<div class="article">
          <h3 id="{anchor}">{icon} {article['header']} <a href="{article['url']}" target="_blank">LINK</a></h3>
          <ul>'''
        # Try to split summary into bullet points if possible
        summary = article['summary']
        bullets = [s.strip() for s in summary.split('\n') if s.strip()]
        if len(bullets) > 1:
            for bullet in bullets:
                main_html += f'<li>{bullet}</li>'
        else:
            main_html += f'<li>{summary}</li>'
        main_html += '</ul></div>'
    # Social icons (optional, can add your own links)
    social_html = '''<div class="social-icons">
      <a href="https://twitter.com/"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/x.svg" alt="X" /></a>
      <a href="https://instagram.com/"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/instagram.svg" alt="Instagram" /></a>
      <a href="https://github.com/"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/github.svg" alt="GitHub" /></a>
      <a href="https://spotify.com/"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/spotify.svg" alt="Spotify" /></a>
    </div>'''
    # Full HTML
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">{style}</head><body style="background:#181a1b;">
<div class="newsletter-container">
  <div class="header">
    <div class="date">{date_str}</div>
    <!-- <img src="https://yourdomain.com/logo.png" alt="Logo" style="height:48px;margin-bottom:8px;" /> -->
    <h1>Your Daily AI Newsletter</h1>
    <div class="greeting">Hi there, this is your daily AI Newsletter.</div>
  </div>
  <div class="toc">
    <h2>In today's newsletter:</h2>
    <ul>{''.join(toc_items)}</ul>
  </div>
  <div class="main">{main_html}</div>
  <div class="footer">
    {social_html}
    <div style="margin-top:8px;">Not subscribed? <a href="#">Subscribe for free</a></div>
    <div style="margin-top:8px;">Update your email preferences or <a href="#">unsubscribe here</a></div>
    <div style="margin-top:8px;">© {datetime.now().year} Your Newsletter</div>
  </div>
</div>
</body></html>'''
    return html

def create_and_send_newsletters(newsletters: Dict[str, Dict[str, Any]]):
    today = datetime.now(UTC).date()
    for user_id, newsletter in newsletters.items():
        # Fetch user email from Firestore
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            print(f"User {user_id} not found.")
            continue
        user_email = user_doc.to_dict().get('email')
        if not user_email:
            print(f"No email for user {user_id}")
            continue
        html_content = render_newsletter_html(newsletter)
        subject = f"Your AI Newsletter for {today}"
        response = send_newsletter_mailgun(user_email, subject, html_content)
        if response and response.status_code == 200:
            print(f"✅ Newsletter sent to {user_email}")
            # Mark as delivered in Firestore
            db.collection('newsletters').document(f"{user_id}_{today}").update({"delivered": True})
        else:
            print(f"❌ Failed to send newsletter to {user_email}: {response.text if response else 'No response'}")


# --- Main Pipeline Orchestrator ---
def main():
    """Main AI pipeline orchestrator."""
    print("🚀 Starting AI Newsletter Pipeline")
    print("=" * 50)
    
    api_token = os.getenv('THENEWS_API_TOKEN')
    if not api_token:
        print("THENEWS_API_TOKEN not found in environment variables. Cannot fetch news.")
        return

    topics = ['general', 'science', 'sports', 'tech', 'entertainment']
    
    # Step 1 & 2: Fetch and Summarize Articles for each topic
    print("\n📰 Step 1 & 2: Fetching and Summarizing Articles...")
    for topic in topics:
        articles = fetch_articles_for_topic(topic, api_token)
        summaries = []
        if articles:
            for article_data in articles:
                summary = summarize_article(article_data, topic)
                if summary:
                    summaries.append(summary)
        store_summaries(topic, summaries)

    # Step 3: Get user preferences
    print("\n👥 Step 3: Getting user preferences...")
    user_preferences = get_user_preferences()
    
    if not user_preferences:
        print("❌ No users with preferences found. Exiting.")
        return
    
    # Step 4: Create personalized newsletters
    print("\n📧 Step 4: Creating personalized newsletters...")
    newsletters = {}
    for user_id, user_topics in user_preferences.items():
        newsletter = create_personalized_newsletter(user_id, user_topics)
        if newsletter['total_articles'] > 0:
            newsletters[user_id] = newsletter
    
    # Step 5: Store newsletters in Firestore
    print("\n💾 Step 5: Storing newsletters in Firestore...")
    if newsletters:
        store_newsletters_in_firestore(newsletters)
    else:
        print("❌ No newsletters were created.")
    
    # Step 6: Send newsletters via Mailgun
    print("\n✉️ Step 6: Sending newsletters via Mailgun...")
    create_and_send_newsletters(newsletters)
    
    print("\n🎉 AI Pipeline completed successfully!")
    print(f"📊 Summary: Created {len(newsletters)} personalized newsletters and sent emails.")

if __name__ == "__main__":
    main()

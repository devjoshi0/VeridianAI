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
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

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

# Remove Mailgun environment variables
# Add Brevo environment variables
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'AI Newsletter')

def send_newsletter_brevo(to_email, subject, html_content):
    if not (BREVO_API_KEY and BREVO_SENDER_EMAIL):
        print("Brevo environment variables not set.")
        return False
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"email": BREVO_SENDER_EMAIL, "name": BREVO_SENDER_NAME},
        subject=subject,
        html_content=html_content
    )
    try:
        response = api_instance.send_transac_email(send_smtp_email)
        print("Brevo response:", response)
        return response
    except ApiException as e:
        print(f"❌ Failed to send newsletter to {to_email}: {e}")
        return None

def render_newsletter_html(newsletter, compatibility_mode=False):
    """
    Renders the newsletter HTML.
    If compatibility_mode is True, uses a table-based, light-background template for maximum email compatibility.
    If False, uses a modern look (light background, dark text, no external images).
    """
    topic_icons = {
        'science': '🔬',
        'sports': '🏅',
        'tech': '💻',
        'entertainment': '🎬',
        'general': '📰',
    }
    from datetime import datetime
    date_str = datetime.strptime(newsletter['date'], '%Y-%m-%d').strftime('%A %d %B %Y')
    toc_items = []
    article_anchors = []
    anchor_count = 1
    for section in newsletter['sections']:
        icon = topic_icons.get(section['topic'], '📰')
        for article in section['articles']:
            anchor = f"article{anchor_count}"
            toc_items.append((anchor, icon, article))
            article_anchors.append((anchor, icon, article))
            anchor_count += 1

    if compatibility_mode:
        # Table-based, maximum compatibility template
        toc_rows = [f'<tr><td style="padding:2px 0;font-size:15px;">{icon} <a href="#{anchor}" style="color:#1a73e8;text-decoration:none;">{article["header"]}</a></td></tr>' for anchor, icon, article in toc_items]
        main_html = ""
        for anchor, icon, article in article_anchors:
            summary = article['summary']
            bullets = [s.strip() for s in summary.split('\n') if s.strip()]
            bullet_html = "".join([f"<li>{b}</li>" for b in bullets]) if len(bullets) > 1 else f"<li>{summary}</li>"
            main_html += f"""
            <tr>
                <td style=\"padding:16px 0 0 0;\">
                    <h3 id=\"{anchor}\" style=\"margin:0 0 8px 0;font-size:20px;color:#222;\">{icon} {article['header']} <a href=\"{article['url']}\" target=_blank style=\"color:#1a73e8;text-decoration:none;\">LINK</a></h3>
                    <ul style=\"margin:0 0 0 20px;padding:0;color:#333;\">{bullet_html}</ul>
                </td>
            </tr>
            """
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\">
  <title>Your Daily AI Newsletter</title>
</head>
<body style=\"background:#f7f7f7;margin:0;padding:0;\">
  <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" style=\"background:#f7f7f7;\">
    <tr>
      <td align=\"center\">
        <table width=\"600\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" style=\"background:#fff;border-radius:8px;box-shadow:0 2px 8px #0001;margin:24px 0;\">
          <tr>
            <td style=\"padding:24px 24px 8px 24px;text-align:center;\">
              <div style=\"color:#888;font-size:14px;margin-bottom:8px;\">{date_str}</div>
              <h1 style=\"margin:0 0 8px 0;font-size:28px;color:#222;\">Your Daily AI Newsletter</h1>
              <div style=\"font-size:16px;color:#444;margin-bottom:16px;\">Hi there, this is your daily AI Newsletter.</div>
            </td>
          </tr>
          <tr>
            <td style=\"background:#f0f0f0;padding:16px 24px;border-bottom:1px solid #eee;\">
              <h2 style=\"font-size:18px;color:#222;margin:0 0 8px 0;\">In today's newsletter:</h2>
              <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\">{''.join(toc_rows)}</table>
            </td>
          </tr>
          {main_html}
          <tr>
            <td style=\"background:#f0f0f0;color:#888;text-align:center;font-size:13px;padding:16px 24px;border-top:1px solid #eee;\">
              <div style=\"margin-top:8px;\">Not subscribed? <a href=\"#\" style=\"color:#1a73e8;text-decoration:underline;\">Subscribe for free</a></div>
              <div style=\"margin-top:8px;\">Update your email preferences or <a href=\"#\" style=\"color:#1a73e8;text-decoration:underline;\">unsubscribe here</a></div>
              <div style=\"margin-top:8px;\">© {datetime.now().year} Your Newsletter</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        return html
    else:
        # Modern look, light background, dark text, no external images
        style = '''
        <style>
          body { font-family: Arial, sans-serif; background: #f7f7f7; color: #222; margin: 0; padding: 0; }
          .newsletter-container { max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px #0001; }
          .header { background: #f7f7f7; padding: 24px 24px 8px 24px; text-align: center; }
          .header .date { color: #888; font-size: 14px; margin-bottom: 8px; }
          .header h1 { margin: 0 0 8px 0; font-size: 28px; color: #222; }
          .greeting { font-size: 16px; color: #444; margin-bottom: 16px; }
          .toc { background: #f0f0f0; padding: 16px 24px; border-bottom: 1px solid #eee; }
          .toc h2 { font-size: 18px; color: #222; margin: 0 0 8px 0; }
          .toc ul { padding-left: 20px; margin: 0; }
          .toc li { font-size: 15px; margin-bottom: 4px; color: #222; }
          .main { padding: 24px; }
          .article { margin-bottom: 32px; }
          .article h3 { margin: 0 0 8px 0; font-size: 20px; color: #222; }
          .article a { color: #1a73e8; text-decoration: none; }
          .article ul { margin: 0 0 0 20px; color: #333; }
          .footer { background: #f7f7f7; color: #888; text-align: center; font-size: 13px; padding: 16px 24px; border-top: 1px solid #eee; }
          .footer a { color: #1a73e8; text-decoration: underline; }
        </style>
        '''
        toc_html = ''.join([f'<li>{icon} <a href="#{anchor}" style="color:#1a73e8;text-decoration:none;">{article["header"]}</a></li>' for anchor, icon, article in toc_items])
        main_html = ""
        for anchor, icon, article in article_anchors:
            summary = article['summary']
            bullets = [s.strip() for s in summary.split('\n') if s.strip()]
            if len(bullets) > 1:
                bullet_html = ''.join([f'<li>{b}</li>' for b in bullets])
            else:
                bullet_html = f'<li>{summary}</li>'
            main_html += f'''<div class="article">
              <h3 id="{anchor}">{icon} {article['header']} <a href="{article['url']}" target="_blank">LINK</a></h3>
              <ul>{bullet_html}</ul>
            </div>'''
        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">{style}</head><body style="background:#f7f7f7;">
<div class="newsletter-container">
  <div class="header">
    <div class="date">{date_str}</div>
    <h1>Your Daily AI Newsletter</h1>
    <div class="greeting">Hi there, this is your daily AI Newsletter.</div>
  </div>
  <div class="toc">
    <h2>In today's newsletter:</h2>
    <ul>{toc_html}</ul>
  </div>
  <div class="main">{main_html}</div>
  <div class="footer">
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
        response = send_newsletter_brevo(user_email, subject, html_content)
        if response and hasattr(response, 'message_id'):
            print(f"✅ Newsletter sent to {user_email}")
            # Mark as delivered in Firestore
            db.collection('newsletters').document(f"{user_id}_{today}").update({"delivered": True})
        else:
            print(f"❌ Failed to send newsletter to {user_email}: {response if response else 'No response'}")


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
    
    # Step 6: Send newsletters via Brevo
    print("\n✉️ Step 6: Sending newsletters via Brevo...")
    create_and_send_newsletters(newsletters)
    
    print("\n🎉 AI Pipeline completed successfully!")
    print(f"📊 Summary: Created {len(newsletters)} personalized newsletters and sent emails.")

if __name__ == "__main__":
    main()

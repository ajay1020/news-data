import os
import json
import feedparser
import requests
from datetime import datetime

# 1. Define your curated RSS News Feeds
FEEDS = {
    "TECH": "https://www.theverge.com/rss/index.xml",
    "GAMING": "https://feeds.feedburner.com/ign/news",
    "GENERAL": "https://feeds.bbci.co.uk/news/rss.xml"
}

# 2. Grab your free Gemini API key from GitHub Environments
API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def ask_gemini(article_title, article_summary):
    """Sends raw news to the free Gemini model to get an optimized, 3-bullet summary."""
    prompt = f"""
    You are an expert news editor for a fast-paced mobile app. 
    Analyze this news story:
    Title: {article_title}
    Context: {article_summary}

    Provide an output strictly in the following JSON format. Do not write any markdown prose outside the JSON wrapper.
    {{
        "headline": "A bold, short headline under 8 words summarizing the core event",
        "summary": "• First punchy fact taking under 2 seconds to read.\\n• Second crucial context point.\\n• Third critical takeaway or future outlook."
    }}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=15)
        if response.statusCode == 200:
            raw_text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            # Clean up accidental markdown backticks if the AI provides them
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)
    except Exception as e:
        print(f"AI Optimization failed for story: {e}")
    return None

def main():
    # Load your current live news.json database file
    db_file = "news.json"
    if os.path.exists(db_file):
        with open(db_file, "r") as f:
            try:
                news_database = json.load(f)
            except:
                news_database = []
    else:
        news_database = []

    # Get a list of headlines already published to avoid repeating news
    existing_headlines = {item["headline"] for item in news_database}
    new_stories_added = 0

    # Scrape feeds
    for category, url in FEEDS.items():
        print(f"Scraping {category} feed...")
        feed = feedparser.parse(url)
        
        # Check the top latest breaking article from each feed
        if not feed.entries:
            continue
            
        latest_entry = feed.entries[0]
        title = latest_entry.title
        link = latest_entry.link
        description = getattr(latest_entry, 'summary', title)

        # Let the AI process it if it's completely fresh news
        ai_data = ask_gemini(title, description)
        if ai_data and ai_data["headline"] not in existing_headlines:
            current_time = datetime.now().strftime("%b %d • %I:%M %p")
            
            new_item = {
                "headline": ai_data["headline"],
                "summary": ai_data["summary"],
                "category": category,
                "link": link,
                "date": current_time
            }
            
            # Inject right at the top of the app feed database
            news_database.insert(0, new_item)
            new_stories_added += 1
            print(f"Successfully posted: {ai_data['headline']}")

    # Keep database running fast by capping it at the 40 freshest stories
    news_database = news_database[:40]

    # Save updates back into your repository database file
    if new_stories_added > 0:
        with open(db_file, "w") as f:
            json.dump(news_database, f, indent=2)
    else:
        print("No new breaking updates found during this cycle.")

if __name__ == "__main__":
    main()

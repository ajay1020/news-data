import os
import json
import re
import feedparser
import google.generativeai as genai
from datetime import datetime

# Initialize Gemini Client cleanly using standard Actions Environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY secret is completely missing from repository settings.")
    exit(1)

genai.configure(api_key=api_key)

FEEDS = {
    "TECH": "https://www.theverge.com/rss/index.xml",
    "GAMING": "https://www.ign.com/rss/articles/feed",
    "GENERAL": "http://feeds.bbci.co.uk/news/rss.xml"
}

def clean_html(text):
    return re.sub('<[^<]+?>', '', text).strip()

def summarize_story(headline, text, category):
    prompt = f"""
    You are the core optimization engine for a fast-paced mobile news app.
    Analyze this breaking story title and description. Compress it into exactly 3 highly readable, punchy bullet points that take under 5 seconds to scan. 
    Clean out any html fragments or raw web links.
    
    Story: {headline} - {text}
    """
    try:
        # Utilizing an active production generation model name
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Accessing raw text directly without non-existent .statusCode metrics
        if response and response.text:
            bullets = response.text.strip().split('\n')
            clean_bullets = [re.sub(r'^[\*\-\s\d\.]+', '', b).strip() for b in bullets if b.strip()][:3]
            while len(clean_bullets) < 3:
                clean_bullets.append("Read full coverage at the original source link.")
            return clean_bullets
    except Exception as e:
        print(f"Gemini Handoff failed for this item: {str(e)}")
    return None

def main():
    print("Initializing Autopilot News Scraper Engine...")
    master_news = []
    
    for category, url in FEEDS.items():
        print(f"Scraping active {category} feed stream...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:3]: # Grab top items per stream
            title = entry.get('title', '')
            summary_raw = clean_html(entry.get('summary', entry.get('description', '')))
            link = entry.get('link', '')
            
            if not title or not link:
                continue
                
            optimized_bullets = summarize_story(title, summary_raw, category)
            
            if optimized_bullets:
                print(f"Successfully optimized breaking item for {category}!")
                master_news.append({
                    "headline": title,
                    "summary": ". ".join(optimized_bullets) + ".",
                    "link": link,
                    "category": category,
                    "date": datetime.now().strftime("%b %d • %I:%M %p")
                })
                break # Move to next category once we grab a fresh story
                
    if master_news:
        print("Saving live compiled stories straight to the news.json database...")
        with open('news.json', 'w') as f:
            json.dump(master_news, f, indent=4)
        print("Database sync complete!")
    else:
        print("No new updates generated this cycle. Fallback parameters untouched.")

if __name__ == "__main__":
    main()

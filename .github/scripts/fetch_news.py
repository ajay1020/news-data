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
    return re.sub("<[^<]+?>", "", text).strip()

def clean_markdown_json(text):
    """
    Cleans out markdown wrapper code blocks (like ```json ... ```)
    using stable string slicing. This is 100% copy-paste safe.
    """
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def main():
    print("Initializing Super-Consolidated News Scraper Engine...")
    
    # 1. Gather all raw items across all feeds first
    all_raw_items = []
    for category, url in FEEDS.items():
        print(f"Scraping {category} RSS feed...")
        feed = feedparser.parse(url)
        # Pull the top 4 stories per category to keep the prompt balanced
        for entry in feed.entries[:4]:
            title = entry.get("title", "")
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            if title and link:
                all_raw_items.append({
                    "title": title,
                    "text": summary,
                    "link": link,
                    "category": category
                })

    if not all_raw_items:
        print("No articles found across any RSS feeds. Exiting.")
        return

    # 2. Bundle everything into EXACTLY ONE prompt to save daily API quota
    prompt = f"""
    You are the optimization engine for a mobile news app.
    Analyze the following list of news articles from different categories.
    For each item, generate exactly 3 short, punchy bullet points summarizing the story.
    
    You MUST return the response ONLY as a valid JSON array of objects matching this structure:
    [
        {{
            "headline": "Original Title or Cleaned Headline",
            "summary": "Bullet point 1. Bullet point 2. Bullet point 3.",
            "link": "Original source link matching the entry",
            "category": "The matching category (TECH, GAMING, or GENERAL)"
        }}
    ]
    Do not wrap the JSON response in code blocks. Return raw JSON text only.
    
    Articles list to process:
    {json.dumps(all_raw_items, indent=2)}
    """

    print("Sending single consolidated batch request to Gemini API...")
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        if response and response.text:
            clean_text = clean_markdown_json(response.text)
            parsed_results = json.loads(clean_text)
            
            # Inject timestamps into all parsed items
            current_time = datetime.now().strftime("%b %d • %I:%M %p")
            for item in parsed_results:
                item["date"] = current_time
            
            # Write only if we have compiled articles
            if parsed_results:
                print(f"Successfully processed {len(parsed_results)} articles!")
                print("Saving compiled stories directly to news.json...")
                with open("news.json", "w") as f:
                    json.dump(parsed_results, f, indent=4)
                print("Database sync complete!")
                return
                
    except Exception as e:
        print(f"Gemini Consolidated Handoff failed: {str(e)}")
        
    print("No updates generated during this cycle. Existing database preserved.")

if __name__ == "__main__":
    main()

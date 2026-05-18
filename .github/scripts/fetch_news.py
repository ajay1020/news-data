import os
import json
import re
import time
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
    using stable, simple string splicing instead of complex regex.
    This prevents any mobile copy-paste syntax errors!
    """
    text = text.strip()
    
    # Strip opening backticks block
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline:].strip()
            
    # Strip closing backticks block
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text

def process_batch_feed(category, entries):
    """
    Bundles multiple RSS headlines and description feeds into a single payload request.
    This safely protects your 20 daily free requests ceiling.
    """
    batch_input = []
    for idx, entry in enumerate(entries):
        title = entry.get("title", "")
        summary = clean_html(entry.get("summary", entry.get("description", "")))
        link = entry.get("link", "")
        if title and link:
            batch_input.append({
                "id": idx,
                "title": title,
                "text": summary,
                "link": link
            })
            
    if not batch_input:
        return []

    prompt = f"""
    You are the optimization engine for a mobile news application.
    Analyze the following list of news articles for the category '{category}'.
    For every article in the list, generate exactly 3 short, punchy bullet points summarizing the story.
    
    Return the response ONLY as a valid JSON array of objects, matching this exact structure:
    [
        {{
            "headline": "Original Title or Cleaned Headline",
            "summary": "Bullet point 1. Bullet point 2. Bullet point 3.",
            "link": "Original source link matching the entry",
            "category": "{category}"
        }}
    ]
    Do not wrap the JSON response in code blocks. Return raw JSON text only.
    
    Articles list to process:
    {json.dumps(batch_input, indent=2)}
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        if response and response.text:
            # Safely clean out any structural code fences
            clean_text = clean_markdown_json(response.text)
            parsed_results = json.loads(clean_text)
            
            # Inject standard timestamp dates to all processed items
            current_time = datetime.now().strftime("%b %d • %I:%M %p")
            for item in parsed_results:
                item["date"] = current_time
            return parsed_results
            
    except Exception as e:
        print(f"Gemini Batch process failed for category {category}: {str(e)}")
    return []

def main():
    print("Initializing Batch-Processing News Scraper Engine...")
    master_news = []
    
    for category, url in FEEDS.items():
        print(f"Scraping active {category} feed stream...")
        feed = feedparser.parse(url)
        
        # Batch collect top 8 stories per category
        target_entries = feed.entries[:8]
        
        # Pulls up to 8 summaries concurrently inside a single API transaction
        batch_stories = process_batch_feed(category, target_entries)
        master_news.extend(batch_stories)
        
        # Small network pacing safety delay
        time.sleep(2)
                
    if master_news:
        print(f"Saving {len(master_news)} live batch-compiled stories straight to the news.json database...")
        with open("news.json", "w") as f:
            json.dump(master_news, f, indent=4)
        print("Database sync complete!")
    else:
        print("No new updates generated during this batch run execution loop.")

if __name__ == "__main__":
    main()

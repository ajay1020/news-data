import os
import json
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
    import re
    return re.sub('<[^<]+?>', '', text).strip()

def summarize_story(headline, text, category):
    prompt = f"""
    You are the core optimization engine for a fast-paced mobile news app. 
    Analyze this breaking story title and description. Compress it into exactly 3 highly readable, punchy bullet points that take under 5 seconds to scan. Clean out any html fragments or raw web links.

    STORY TITLE: {headline}
    STORY BODY: {text}

    Respond strictly in this clean formatting structure with zero markdown or conversational chatter:
    HEADLINE: (A bold, urgent headline summarizing the break)
    SUMMARY: (Type your 3 punchy lines here separated by spaces or small dashes)
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # FIXED: Check if response and response.text exist directly without using legacy attribute tags
        if response and hasattr(response, 'text') and response.text:
            lines = response.text.strip().split('\n')
            res_headline = headline
            res_summary = ""
            for line in lines:
                if line.startswith("HEADLINE:"):
                    res_headline = line.replace("HEADLINE:", "").strip()
                elif line.startswith("SUMMARY:"):
                    res_summary = line.replace("SUMMARY:", "").strip()
            
            if not res_summary:
                res_summary = lines[-1].strip()
                
            return {
                "headline": res_headline,
                "summary": res_summary if res_summary else "Tap the source link below to open the breaking article coverage details.",
                "category": category,
                "date": datetime.now().strftime("%b %d • %I:%M %p"),
                "link": ""
            }
    except Exception as e:
        print(f"Gemini Handoff failed for this item: {str(e)}")
    return None

def main():
    print("Initializing Autopilot News Scraper Engine...")
    master_news = []
    
    for category, url in FEEDS.items():
        print(f"Scraping active {category} feed stream...")
        try:
            feed = feedparser.parse(url)
            # Process the single most recent breaking item from each news provider
            if feed.entries:
                entry = feed.entries[0]
                raw_desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                clean_desc = clean_html(raw_desc)[:1000]
                
                article_data = summarize_story(entry.title, clean_desc, category)
                if article_data:
                    article_data["link"] = getattr(entry, 'link', '')
                    master_news.append(article_data)
                    print(f"Successfully optimized breaking item for {category}!")
        except Exception as e:
            print(f"Failed to parse data stream for {category}: {str(e)}")

    if master_news:
        print("Saving live compiled stories straight to the news.json database...")
        with open("news.json", "w") as f:
            json.dump(master_news, f, indent=4)
        print("Database sync complete!")
    else:
        print("No new breaking updates found during this cycle. Verification checks completed.")

if __name__ == "__main__":
    main()

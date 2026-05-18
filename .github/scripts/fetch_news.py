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
    return re.sub('<[^<]+?>', '', text).strip()

def process_batch_feed(category, entries):
    """
    Bundles multiple articles into a single API payload request.
    This preserves your 20 daily request quota.
    """
    # Create an isolated structure template for the AI to replicate
    batch_input = []
    for idx, entry in enumerate(entries):
        title = entry.get('title', '')
        summary = clean_html(entry.get('summary', entry.get('description', '')))
        link = entry.get('link', '')
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
     Do not wrap the JSON response in ```json code blocks. Return raw text only.
    
    Articles list to process:
    {json.dumps(batch_input, indent=2)}
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        if response and response.text:
            # Clean off any accidental markdown wrapper characters if left over
            clean_text = response.text.strip()
            if clean_text.startswith("```"):
                clean_text = re.sub(r'^
http://googleusercontent.com/immersive_entry_chip/0

---

## ⚡ Force the Upgraded Production Deployment

1. Scroll straight down to the absolute bottom edge of your GitHub web page view and click the green **Commit changes** button to lock it in.
2. Tap your repository's horizontal **Actions** tab option bar row at the top of your layout.
3. Choose **"Auto Pilot Fast News Updater"** from the left track list.
4. Click the gray **"Run workflow"** dropdown container button on the right side and hit the green activation choice.

### 📱 What Changes Inside Your App Layout?
Because this script processes articles concurrently, it uses only 3 total API requests out of your 20-request daily ceiling per deployment run. Once the workflow turns into a solid green checkmark, open your **FAST NEWS** application launcher, tap your 🔄 **Action Button**, and watch a deep, uncapped stream of real-time articles fill your dark-mode UI container layout grids!

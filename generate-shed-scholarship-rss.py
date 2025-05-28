import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone, timedelta
import hashlib
import time
import sys

# --- Configuration ---
SCHOLARSHIP_URL = "https://shed.gov.bd/site/view/scholarship/%E0%A6%B6%E0%A6%BF%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A6%BE%E0%A6%AC%E0%A7%83%E0%A6%A4%E0%A7%8D%E0%A6%A4%E0%A6%BF-%E0%A6%AC%E0%A6%BF%E0%A6%9C%E0%A7%8D%E0%A6%9E%E0%A6%AA%E0%A7%8D%E0%A6%A4%E0%A6%BF"
RSS_FILENAME = "shed_scholarship_feed.xml"
FEED_TITLE = "Bangladesh MoE Scholarship Notices"
FEED_LINK = SCHOLARSHIP_URL
FEED_DESCRIPTION = "Latest scholarship notices from the Secondary and Higher Education Division, Ministry of Education, Bangladesh."
MAX_FEED_ITEMS = 50
LOCAL_TIMEZONE = timezone(timedelta(hours=6))  # Bangladesh time

def fetch_scholarship_notices():
    """Fetches scholarship notices with error handling and retry logic."""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            resp = requests.get(SCHOLARSHIP_URL, headers=headers, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            
            soup = BeautifulSoup(resp.text, "lxml")
            notices = []

            table = soup.find("table")
            if not table:
                print("No table found on the page.")
                return []

            for row in table.find_all("tr")[1:]:  # Skip header
                try:
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue
                        
                    title = cols[1].get_text(strip=True)
                    date_str = cols[2].get_text(strip=True)
                    link_tag = cols[3].find("a")
                    link = link_tag["href"] if link_tag and link_tag.has_attr("href") else SCHOLARSHIP_URL

                    # Parse date (format: YYYY-MM-DD or DD-MM-YYYY)
                    try:
                        if "-" in date_str:
                            if date_str[2] == "-":
                                pub_date = datetime.strptime(date_str, "%d-%m-%Y")
                            else:
                                pub_date = datetime.strptime(date_str, "%Y-%m-%d")
                        else:
                            pub_date = datetime.now()
                    except Exception:
                        pub_date = datetime.now()
                        
                    # Set time to current local time
                    now_bd = datetime.now(LOCAL_TIMEZONE)
                    pub_date = pub_date.replace(hour=now_bd.hour, minute=now_bd.minute, second=now_bd.second, tzinfo=LOCAL_TIMEZONE)
                    pub_date_utc = pub_date.astimezone(timezone.utc)

                    guid = hashlib.sha1((title + link).encode("utf-8")).hexdigest()
                    notices.append({
                        "title": title,
                        "link": link,
                        "pub_date": pub_date_utc,
                        "guid": guid,
                        "description": title
                    })
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
                    
            print(f"Successfully fetched {len(notices)} scholarship notices.")
            return notices
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Error fetching scholarship notices: {e}. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Error fetching scholarship notices after {max_retries} attempts: {e}")
                return []
        except Exception as e:
            print(f"Unexpected error while processing scholarship notices: {e}")
            return []
    
    return []

def generate_rss_feed(notices, filename):
    """Generates RSS feed with error handling."""
    try:
        root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = FEED_TITLE
        ET.SubElement(channel, "link").text = FEED_LINK
        ET.SubElement(channel, "description").text = FEED_DESCRIPTION
        ET.SubElement(channel, "language").text = "bn-BD"
        ET.SubElement(channel, "copyright").text = "Ministry of Education, Bangladesh"
        ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        
        for item in notices[:MAX_FEED_ITEMS]:
            entry = ET.SubElement(channel, "item")
            ET.SubElement(entry, "title").text = item["title"]
            ET.SubElement(entry, "link").text = item["link"]
            ET.SubElement(entry, "description").text = item["description"]
            ET.SubElement(entry, "pubDate").text = item["pub_date"].strftime("%a, %d %b %Y %H:%M:%S %z")
            ET.SubElement(entry, "guid").text = item["guid"]
            
        xml_str = ET.tostring(root, encoding="utf-8")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8")
        
        with open(filename, "wb") as f:
            f.write(pretty_xml)
        print(f"RSS feed generated: {filename}")
        
    except Exception as e:
        print(f"Error generating RSS feed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        print("Starting shed.gov.bd scholarship RSS feed generation...")
        notices = fetch_scholarship_notices()
        if notices:
            generate_rss_feed(notices, RSS_FILENAME)
        else:
            print("No notices found.")
    except Exception as e:
        print(f"Unexpected error during execution: {e}")
        sys.exit(1)

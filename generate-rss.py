import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
import os
import hashlib

# --- Configuration ---
NOTICE_URL = "https://aust.edu/notice"
# IMPORTANT: Inspect the website's HTML to find the right selector.
# This selector assumes notices are in <li> tags inside a <div> with class 'list-content'.
# You *will* likely need to change this if the website structure is different or changes.
NOTICE_SELECTOR = "div.list-content ul li" # Example selector - ADJUST AS NEEDED
RSS_FILENAME = "feed.xml"
MAX_FEED_ITEMS = 50 # Maximum number of items to keep in the feed
FEED_TITLE = "AUST Notice Board Updates"
FEED_LINK = NOTICE_URL
FEED_DESCRIPTION = "Latest notices from the Ahsanullah University of Science and Technology notice board."
# --- End Configuration ---

def fetch_notices():
    """Fetches and parses notices from the AUST notice page."""
    try:
        response = requests.get(NOTICE_URL, timeout=20)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {NOTICE_URL}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'lxml') # Use lxml for better parsing
    # --- Find notice elements based on the selector ---
    # !! This is the most likely part to break if the website changes !!
    notice_elements = soup.select(NOTICE_SELECTOR)
    # --- ---

    if not notice_elements:
        print(f"Warning: No notice elements found using selector '{NOTICE_SELECTOR}'. Website structure might have changed.")
        # Try a broader selector as a fallback? (Example: just 'li')
        # notice_elements = soup.select('li')
        # if not notice_elements:
        #     print("Fallback selector also found nothing.")
        #     return []

    notices = []
    for element in notice_elements:
        title = element.get_text(strip=True)
        link_tag = element.find('a')
        link = link_tag['href'] if link_tag and link_tag.get('href') else NOTICE_URL # Fallback link

        # Try to make the link absolute if it's relative
        if link and not link.startswith(('http://', 'https://')):
             # Requires urljoin, let's import it if needed
             from urllib.parse import urljoin
             link = urljoin(NOTICE_URL, link)


        # Use a hash of the title and link as a stable GUID if link isn't unique per item
        guid_content = f"{title}-{link}"
        guid = hashlib.sha1(guid_content.encode('utf-8')).hexdigest()

        # Attempt to extract a date if available (very site-specific)
        # Example: Look for a span with class 'date' - ADJUST AS NEEDED
        # date_tag = element.find('span', class_='date')
        # pub_date_str = date_tag.get_text(strip=True) if date_tag else None
        pub_date = datetime.now(timezone.utc) # Fallback to now if no date found/parsed
        # Add parsing logic here if date format is known

        if title: # Only add if we actually got a title
            notices.append({
                'title': title,
                'link': link,
                'guid': guid,
                'pub_date': pub_date,
            })
    return notices

def load_existing_feed_guids(filename):
    """Loads GUIDs from an existing RSS feed file."""
    existing_guids = set()
    if not os.path.exists(filename):
        return existing_guids

    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for item in root.findall('./channel/item'):
            guid = item.find('guid')
            if guid is not None:
                existing_guids.add(guid.text)
    except ET.ParseError:
        print(f"Warning: Could not parse existing feed file {filename}. Starting fresh.")
    except FileNotFoundError:
         print(f"No existing feed file found at {filename}. Starting fresh.") # Should be caught by os.path.exists, but belt-and-suspenders
    return existing_guids

def generate_rss_feed(notices, existing_guids, filename):
    """Generates and saves the RSS feed XML file."""
    root = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
    channel = ET.SubElement(root, "channel")

    # Add Atom self-link (optional but good practice)
    # Assumes hosting on GitHub Pages, replace <username> and <repository>
    # You might need to get this from Action environment variables if you want it perfect
    gh_pages_url = f"https://<YOUR_USERNAME>.github.io/<YOUR_REPOSITORY>/{filename}"
    atom_link = ET.SubElement(channel, "atom:link", href=gh_pages_url, rel="self", type="application/rss+xml")


    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESCRIPTION
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

    # Add new items first
    new_items_added = 0
    combined_items = []

    for notice in notices:
        if notice['guid'] not in existing_guids:
            item = ET.Element("item")
            ET.SubElement(item, "title").text = notice['title']
            ET.SubElement(item, "link").text = notice['link']
            ET.SubElement(item, "description").text = notice['title'] # Use title as description or add more detail if possible
            ET.SubElement(item, "pubDate").text = notice['pub_date'].strftime("%a, %d %b %Y %H:%M:%S %z")
            ET.SubElement(item, "guid", isPermaLink="false").text = notice['guid'] # isPermaLink=false if GUID is not the URL
            combined_items.append(item)
            new_items_added += 1

    print(f"Found {len(notices)} notices on page. Added {new_items_added} new item(s).")

    # Add old items, ensuring not to exceed MAX_FEED_ITEMS
    if os.path.exists(filename):
        try:
            tree = ET.parse(filename)
            old_root = tree.getroot()
            for old_item in old_root.findall('./channel/item'):
                 # Check if we need more items and if the item isn't already added (edge case)
                guid_elem = old_item.find('guid')
                if len(combined_items) < MAX_FEED_ITEMS and guid_elem is not None and guid_elem.text not in [elem.find('guid').text for elem in combined_items]:
                     combined_items.append(old_item)

        except (ET.ParseError, FileNotFoundError):
             print("Could not parse or find old feed to append items, only new items will be present.")


    # Add the combined items (newest first) to the channel
    for item in combined_items[:MAX_FEED_ITEMS]: # Ensure limit
         channel.append(item)


    # Prettify XML output
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding='utf-8')

    try:
        with open(filename, "wb") as f: # Write in binary mode for UTF-8
            f.write(pretty_xml_str)
        print(f"RSS feed successfully generated and saved to {filename}")
    except IOError as e:
        print(f"Error writing RSS feed file {filename}: {e}")


if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting AUST notice scraping process...")
    fetched_notices = fetch_notices()
    if fetched_notices:
        current_guids = load_existing_feed_guids(RSS_FILENAME)
        generate_rss_feed(fetched_notices, current_guids, RSS_FILENAME)
    else:
        print("No notices fetched. RSS feed generation skipped.")
    print(f"[{datetime.now()}] Process finished.")
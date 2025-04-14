import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
import os
import hashlib
from urllib.parse import urljoin # Make sure this is imported

# --- Configuration ---
NOTICE_URL = "https://aust.edu/notice"
# !!! Using the selectors you provided !!!
NOTICE_SELECTOR = "div.card-info"         # Container for each notice item
TITLE_SELECTOR = "h6.news_title_homepage" # Specific selector for the title
SUMMARY_SELECTOR = "p.news_excerpt"       # Specific selector for the summary
# --- End User-Provided Selectors ---
RSS_FILENAME = "feed.xml"
MAX_FEED_ITEMS = 50 # Maximum number of items to keep in the feed
FEED_TITLE = "AUST Notice Board Updates"
FEED_LINK = NOTICE_URL
FEED_DESCRIPTION = "Latest notices from the Ahsanullah University of Science and Technology notice board."
# --- End Configuration ---

def fetch_notices():
    """Fetches and parses notices from the AUST notice page."""
    print(f"Fetching notices from {NOTICE_URL}")
    try:
        # Using a common User-Agent can sometimes help avoid blocking
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(NOTICE_URL, headers=headers, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Successfully fetched page. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {NOTICE_URL}: {e}")
        return []

    print(f"Parsing HTML content using lxml...")
    soup = BeautifulSoup(response.content, 'lxml')

    # --- Find notice elements based on the specific container selector ---
    print(f"Looking for notice elements using selector: '{NOTICE_SELECTOR}'")
    notice_elements = soup.select(NOTICE_SELECTOR)
    # --- ---

    if not notice_elements:
        # This error is less likely now with the correct selector, but good to keep
        print(f"Error: No notice elements found using selector '{NOTICE_SELECTOR}'.")
        print("Double-check the selector or website structure if this persists.")
        return []

    print(f"Found {len(notice_elements)} potential notice elements.")
    notices = []
    for element in notice_elements:
        # --- Extract title using the specific selector ---
        title_tag = element.select_one(TITLE_SELECTOR)
        title = title_tag.get_text(strip=True) if title_tag else None

        # --- Extract summary using the specific selector ---
        summary_tag = element.select_one(SUMMARY_SELECTOR)
        summary = summary_tag.get_text(strip=True) if summary_tag else '' # Use empty string if no summary

        # --- Extract the link (assuming it's the first <a> tag within the card) ---
        link_tag = element.find('a') # Find the first link within the card
        link = None
        if link_tag and link_tag.get('href'):
            link = link_tag['href']
            # Make the link absolute if it's relative
            if not link.startswith(('http://', 'https://')):
                link = urljoin(NOTICE_URL, link)
        else:
            print(f"Warning: Could not find <a> tag with href in element for title: '{title}'. Using main notice page URL.")
            link = NOTICE_URL # Fallback link

        # --- Use the Link as GUID if possible (more reliable) ---
        if link and link != NOTICE_URL: # Ensure link is not None before comparing
            guid = link
            is_permalink = True
        else:
            # Fallback GUID if no unique link found
            guid_content = f"{title}-{summary}" # Use title and summary for more uniqueness
            guid = hashlib.sha1(guid_content.encode('utf-8')).hexdigest()
            is_permalink = False

        # --- Attempt to extract a date ---
        # This still requires inspecting the HTML for where the date is located within div.card-info
        # Example: date_tag = element.find('span', class_='date-class-if-any')
        # If found, parse it, otherwise fallback to now.
        pub_date = datetime.now(timezone.utc) # Fallback to now
        # --- End Date Extraction Placeholder ---

        if title: # Only add if we actually got a title
            # Use the extracted summary, or title if summary was empty
            description = summary if summary else title
            print(f"  -> Found notice: Title='{title}', Link='{link}', GUID='{guid}'")
            notices.append({
                'title': title,
                'link': link,
                'guid': guid,
                'is_permalink': is_permalink,
                'pub_date': pub_date,
                'description': description # Add description field
            })
        else:
             print(f"Warning: Skipping element as no title could be extracted using '{TITLE_SELECTOR}': {element.prettify()[:200]}...")

    print(f"Finished parsing. Extracted {len(notices)} valid notices.")
    return notices

def load_existing_feed_guids(filename):
    """Loads GUIDs from an existing RSS feed file."""
    existing_guids = set()
    if not os.path.exists(filename):
        print(f"No existing feed file found at {filename}. Starting fresh.")
        return existing_guids

    print(f"Loading existing GUIDs from {filename}...")
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for item in root.findall('./channel/item'):
            guid = item.find('guid')
            if guid is not None and guid.text:
                existing_guids.add(guid.text)
        print(f"Loaded {len(existing_guids)} existing GUIDs.")
    except ET.ParseError as e:
        print(f"Warning: Could not parse existing feed file {filename}. Error: {e}. Starting fresh.")
    except FileNotFoundError:
         print(f"File {filename} not found error during parsing. Starting fresh.")
    return existing_guids

def generate_rss_feed(notices, existing_guids, filename):
    """Generates and saves the RSS feed XML file."""
    print("Generating new RSS feed...")
    root = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
    channel = ET.SubElement(root, "channel")

    # Add Atom self-link (optional but good practice)
    # !!! Remember to replace <YOUR_USERNAME> and <YOUR_REPOSITORY> !!!
    gh_pages_url = f"https://<YOUR_USERNAME>.github.io/<YOUR_REPOSITORY>/{filename}" # <-- UPDATE THIS
    atom_link = ET.SubElement(channel, "atom:link", href=gh_pages_url, rel="self", type="application/rss+xml")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESCRIPTION
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    ET.SubElement(channel, "generator").text = "Python RSS Generator Script" # Optional

    # Combine new and old items
    new_items_added = 0
    combined_items_data = []

    # Add new items first
    for notice in notices:
        if notice['guid'] not in existing_guids:
            combined_items_data.append(notice)
            new_items_added += 1

    print(f"Adding {new_items_added} new item(s).")

    # Load old items from the file, ensuring not to exceed MAX_FEED_ITEMS
    num_old_items_to_add = MAX_FEED_ITEMS - new_items_added
    if num_old_items_to_add > 0 and os.path.exists(filename):
        print(f"Loading max {num_old_items_to_add} old items from existing feed...")
        try:
            tree = ET.parse(filename)
            old_root = tree.getroot()
            loaded_old_items = 0
            for old_item in old_root.findall('./channel/item'):
                guid_elem = old_item.find('guid')
                # Check if we need more items and if the item isn't already added (via GUID)
                if guid_elem is not None and guid_elem.text and guid_elem.text not in [item['guid'] for item in combined_items_data]:
                     # Reconstruct the notice dict for sorting/adding
                     old_notice_data = {
                         'title': old_item.find('title').text if old_item.find('title') is not None else '',
                         'link': old_item.find('link').text if old_item.find('link') is not None else FEED_LINK,
                         'guid': guid_elem.text,
                         'is_permalink': guid_elem.get('isPermaLink', 'false') == 'true',
                         'description': old_item.find('description').text if old_item.find('description') is not None else '', # Load old description
                         'pub_date': datetime.now(timezone.utc) # Default/Fallback
                     }
                     # Attempt to parse the date from the old feed
                     pub_date_elem = old_item.find('pubDate')
                     if pub_date_elem is not None and pub_date_elem.text:
                         try:
                             old_notice_data['pub_date'] = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S %z")
                         except ValueError:
                              try:
                                   old_notice_data['pub_date'] = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)
                              except ValueError:
                                   pass # Keep fallback date

                     combined_items_data.append(old_notice_data)
                     loaded_old_items += 1
                     if loaded_old_items >= num_old_items_to_add:
                         break
            print(f"Added {loaded_old_items} old items.")

        except (ET.ParseError, FileNotFoundError) as e:
             print(f"Could not parse or find old feed to append items. Error: {e}. Only new items will be present.")

    # Sort combined items by publication date, newest first
    combined_items_data.sort(key=lambda x: x['pub_date'], reverse=True)

    # Add the combined items (newest first, up to MAX_FEED_ITEMS) to the channel XML
    items_added_to_xml = 0
    for item_data in combined_items_data[:MAX_FEED_ITEMS]: # Ensure limit
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_data['title']
        ET.SubElement(item, "link").text = item_data['link']
        ET.SubElement(item, "description").text = item_data['description'] # Use the stored description
        ET.SubElement(item, "pubDate").text = item_data['pub_date'].strftime("%a, %d %b %Y %H:%M:%S %z")
        ET.SubElement(item, "guid", isPermaLink=str(item_data['is_permalink']).lower()).text = item_data['guid']
        items_added_to_xml +=1

    print(f"Added {items_added_to_xml} total items to the feed XML.")

    # Prettify XML output
    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    try:
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding='utf-8')
    except Exception as parse_err:
        print(f"Warning: Could not prettify XML output using minidom. Error: {parse_err}. Saving raw XML.")
        pretty_xml_str = xml_str

    try:
        with open(filename, "wb") as f: # Write in binary mode for UTF-8
            f.write(pretty_xml_str)
        print(f"RSS feed successfully generated and saved to {filename}")
    except IOError as e:
        print(f"Error writing RSS feed file {filename}: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"[{start_time}] Starting AUST notice scraping process...")
    # Make sure current location context is considered if needed for date parsing, though using UTC is safer.
    print(f"Current time: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}") # Log local time
    fetched_notices = fetch_notices()
    # Regenerate feed even if no new notices, to update timestamp and prune old items, if feed file exists
    if fetched_notices or os.path.exists(RSS_FILENAME):
        current_guids = load_existing_feed_guids(RSS_FILENAME)
        generate_rss_feed(fetched_notices, current_guids, RSS_FILENAME)
    else:
        if not fetched_notices and not os.path.exists(RSS_FILENAME):
            print("No notices fetched and no existing feed file found. RSS feed generation skipped.")

    end_time = datetime.now()
    print(f"[{end_time}] Process finished. Duration: {end_time - start_time}")
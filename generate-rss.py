import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
# Make sure datetime, timezone are imported correctly
from datetime import datetime, timezone, timedelta
import os
import hashlib
from urllib.parse import urljoin
import locale # For parsing month names potentially
import sys
import json
import time
import logging

# --- Logging Configuration ---
LOG_FILE = "rss_generator.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Configuration ---
NOTICE_URL = "https://aust.edu/notice"
NOTICE_SELECTOR = "div.card-info"         # Container for each notice item
TITLE_SELECTOR = "h6.news_title_homepage" # Specific selector for the title
SUMMARY_SELECTOR = "p.news_excerpt"       # Specific selector for the summary
DAY_SELECTOR = "p.day"                    # Selector for the day part of the date
MONTH_SELECTOR = "p.month"                # Selector for the month part of the date
YEAR_SELECTOR = "p.year"                  # Selector for the year part of the date
# !!! --- DATE FORMAT - Updated based on website structure --- !!!
DATE_FORMAT = "%b %d %Y" # <-- Format after components are combined
# --- End User-Provided Selectors ---
RSS_FILENAME = "feed.xml"
MAX_FEED_ITEMS = 50
FEED_TITLE = "AUST Notice Board Updates"
FEED_LINK = NOTICE_URL
FEED_DESCRIPTION = "Latest notices from the Ahsanullah University of Science and Technology notice board."
# Set locale for month name parsing if needed (e.g., English for "Apr")
try:
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'English_United States.1252') # Windows fallback
    except locale.Error:
        logging.warning("Could not set locale for month name parsing. Ensure system locale supports 'en_US'.")
# --- End Configuration ---

# Define the local timezone (Bangladesh Standard Time = UTC+6)
LOCAL_TIMEZONE = timezone(timedelta(hours=6))

# Cache file for storing the last check's content hash
CACHE_FILE = "notice_cache.json"

def check_for_new_content():
    """Checks if there are new notices by comparing page content hash with previous run.
    Returns True if new content is available or cache doesn't exist, False otherwise."""
    
    # Check if we need to force a refresh (weekly)
    force_refresh = False
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                if 'last_check' in cache:
                    last_check = datetime.fromisoformat(cache['last_check'])
                    now = datetime.now(timezone.utc)
                    # Force refresh if last check was more than 7 days ago
                    if (now - last_check).days >= 7:
                        logging.info("Performing weekly forced refresh regardless of content change")
                        force_refresh = True
        except (json.JSONDecodeError, IOError, ValueError) as e:
            logging.warning(f"Could not check last refresh time: {e}")
            
    if force_refresh:
        return True
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try to load previously saved ETag/hash
        cache = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    
                # If we have a Last-Modified, use it for conditional request
                if 'last_modified' in cache:
                    headers['If-Modified-Since'] = cache['last_modified']
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Could not load cache file: {e}")
        
        response = requests.get(NOTICE_URL, headers=headers, timeout=15)
        
        # If the server responds with 304 Not Modified, content hasn't changed
        if response.status_code == 304:
            logging.info("Content not modified since last check")
            return False
            
        # If the request was successful, check content hash
        if response.status_code == 200:
            content_hash = hashlib.md5(response.content).hexdigest()
            
            # If we have a previous hash and it matches, no new content
            if 'content_hash' in cache and cache['content_hash'] == content_hash:
                logging.info("Content hash matches previous check, no new notices")
                return False
                
            # Save new hash and headers for next time
            new_cache = {
                'content_hash': content_hash,
                'last_check': datetime.now(timezone.utc).isoformat()
            }
            
            # Save Last-Modified header if present
            if 'Last-Modified' in response.headers:
                new_cache['last_modified'] = response.headers['Last-Modified']
                
            try:
                with open(CACHE_FILE, 'w') as f:
                    json.dump(new_cache, f)
            except IOError as e:
                logging.warning(f"Could not save cache file: {e}")
                
            logging.info("New content detected, will process notices")
            return True
            
        # For any other response code, assume we should check (to be safe)
        logging.warning(f"Unexpected response code {response.status_code}, proceeding with check")
        return True
        
    except Exception as e:
        logging.error(f"Error checking for new content: {e}")
        # If any error occurs, proceed with processing to be safe
        return True


def fetch_notices():
    """Fetches and parses notices from the AUST notice page."""
    logging.info(f"Fetching notices from {NOTICE_URL}")
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(NOTICE_URL, headers=headers, timeout=30)
            response.raise_for_status()
            logging.info(f"Successfully fetched page. Status code: {response.status_code}")
            break  # Success, exit the retry loop
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                logging.warning(f"Error fetching URL {NOTICE_URL}: {e}. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logging.error(f"Error fetching URL {NOTICE_URL} after {max_retries} attempts: {e}")
                return []

    logging.info(f"Parsing HTML content using lxml...")
    soup = BeautifulSoup(response.content, 'lxml')

    logging.info(f"Looking for notice elements using selector: '{NOTICE_SELECTOR}'")
    notice_elements = soup.select(NOTICE_SELECTOR)

    if not notice_elements:
        logging.error(f"No notice elements found using selector '{NOTICE_SELECTOR}'.")
        return []

    logging.info(f"Found {len(notice_elements)} potential notice elements.")
    notices = []

    for element in notice_elements:
        title_tag = element.select_one(TITLE_SELECTOR)
        title = title_tag.get_text(strip=True) if title_tag else None

        summary_tag = element.select_one(SUMMARY_SELECTOR)
        summary = summary_tag.get_text(strip=True) if summary_tag else ''

        link_tag = element.find('a')
        link = None
        if link_tag and link_tag.get('href'):
            link = link_tag['href']
            if not link.startswith(('http://', 'https://')):
                link = urljoin(NOTICE_URL, link)
        else:
            link = NOTICE_URL

        if link and link != NOTICE_URL:
            guid = link
            is_permalink = True
        else:
            guid_content = f"{title}-{summary}"
            guid = hashlib.sha1(guid_content.encode('utf-8')).hexdigest()
            is_permalink = False

        # ### DATE EXTRACTION START ###
        pub_date = None
        
        # Extract day, month, and year separately
        day_tag = element.select_one(DAY_SELECTOR)
        month_tag = element.select_one(MONTH_SELECTOR)
        year_tag = element.select_one(YEAR_SELECTOR)
        
        if day_tag and month_tag and year_tag:
            day_str = day_tag.get_text(strip=True)
            month_str = month_tag.get_text(strip=True)
            year_str = year_tag.get_text(strip=True)
            
            # Combine the components into a single date string
            date_str = f"{month_str} {day_str} {year_str}"
            logging.info(f"  Assembled date string: '{date_str}' for title '{title}'")
            
            try:
                # Parse the combined date string using the specified format
                local_dt = datetime.strptime(date_str, DATE_FORMAT)
                # Assume the parsed date is in the local timezone (Dhaka UTC+6)
                aware_local_dt = local_dt.replace(tzinfo=LOCAL_TIMEZONE)
                # Convert to UTC for consistency
                pub_date = aware_local_dt.astimezone(timezone.utc)
                logging.info(f"    Successfully parsed date: {pub_date}")
            except ValueError as date_err:
                logging.error(f"    Could not parse date string '{date_str}' with format '{DATE_FORMAT}'. Error: {date_err}")
                # Fallback handled below
        else:
            missing = []
            if not day_tag: missing.append("day")
            if not month_tag: missing.append("month")
            if not year_tag: missing.append("year")
            logging.warning(f"  Could not find date components: {', '.join(missing)} for title '{title}'")

        # Fallback to current time in UTC if date parsing failed
        if pub_date is None:
            pub_date = datetime.now(timezone.utc)
            logging.info(f"    Using current UTC time as fallback pubDate: {pub_date}")

        # ### DATE EXTRACTION END ###

        if title:
            description = summary if summary else title
            logging.info(f"  -> Found notice: Title='{title}', Link='{link}', Date='{pub_date}', GUID='{guid}'")
            notices.append({
                'title': title,
                'link': link,
                'guid': guid,
                'is_permalink': is_permalink,
                'pub_date': pub_date, # Crucial for sorting
                'description': description
            })
        else:
             logging.warning(f"Skipping element as no title could be extracted using '{TITLE_SELECTOR}'")

    logging.info(f"Finished parsing. Extracted {len(notices)} valid notices.")
    return notices


def load_existing_feed_guids(filename):
    """Loads GUIDs from an existing RSS feed file."""
    existing_guids = set()
    if not os.path.exists(filename):
        logging.info(f"No existing feed file found at {filename}. Starting fresh.")
        return existing_guids

    logging.info(f"Loading existing GUIDs from {filename}...")
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for item in root.findall('./channel/item'):
            guid = item.find('guid')
            if guid is not None and guid.text:
                existing_guids.add(guid.text)
        logging.info(f"Loaded {len(existing_guids)} existing GUIDs.")
    except ET.ParseError as e:
        logging.warning(f"Could not parse existing feed file {filename}. Error: {e}. Starting fresh.")
    except FileNotFoundError:
         logging.warning(f"File {filename} not found error during parsing. Starting fresh.")
    return existing_guids

def generate_rss_feed(notices, existing_guids, filename):
    """Generates and saves the RSS feed XML file."""
    logging.info("Generating new RSS feed...")
    root = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
    channel = ET.SubElement(root, "channel")

    # GitHub Pages URL for the RSS feed
    gh_pages_url = f"https://Owais5514.github.io/AUST-rss/{filename}"
    atom_link = ET.SubElement(channel, "atom:link", href=gh_pages_url, rel="self", type="application/rss+xml")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESCRIPTION
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    ET.SubElement(channel, "generator").text = "Python RSS Generator Script"
    # Add a version element that changes with each run using the current timestamp
    current_timestamp = datetime.now().strftime("%Y%m%d.%H%M%S")
    ET.SubElement(channel, "version").text = f"1.0.{current_timestamp}"

    combined_items_data = []
    new_items_added = 0

    for notice in notices:
        if notice['guid'] not in existing_guids:
            combined_items_data.append(notice)
            new_items_added += 1

    logging.info(f"Adding {new_items_added} new item(s) based on GUID comparison.")

    num_old_items_to_add = MAX_FEED_ITEMS - new_items_added
    if num_old_items_to_add > 0 and os.path.exists(filename):
        logging.info(f"Loading max {num_old_items_to_add} old items from existing feed...")
        try:
            tree = ET.parse(filename)
            old_root = tree.getroot()
            loaded_old_items = 0
            for old_item in old_root.findall('./channel/item'):
                guid_elem = old_item.find('guid')
                if guid_elem is not None and guid_elem.text and guid_elem.text not in [item['guid'] for item in combined_items_data]:
                     old_notice_data = {
                         'title': old_item.find('title').text if old_item.find('title') is not None else '',
                         'link': old_item.find('link').text if old_item.find('link') is not None else FEED_LINK,
                         'guid': guid_elem.text,
                         'is_permalink': guid_elem.get('isPermaLink', 'false') == 'true',
                         'description': old_item.find('description').text if old_item.find('description') is not None else '',
                         'pub_date': datetime.now(timezone.utc) # Default/Fallback
                     }
                     pub_date_elem = old_item.find('pubDate')
                     if pub_date_elem is not None and pub_date_elem.text:
                         try: # Try parsing RFC 822 format from existing feed
                             old_notice_data['pub_date'] = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S %z")
                         except ValueError:
                             try: # Fallback without timezone
                                 old_notice_data['pub_date'] = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)
                             except ValueError:
                                 logging.warning(f"Could not parse old date '{pub_date_elem.text}' for GUID {guid_elem.text}. Using current time.")
                     combined_items_data.append(old_notice_data)
                     loaded_old_items += 1
                     if loaded_old_items >= num_old_items_to_add:
                         break
            logging.info(f"Added {loaded_old_items} old items.")
        except (ET.ParseError, FileNotFoundError) as e:
             logging.warning(f"Could not parse or find old feed to append items. Error: {e}.")

    logging.info(f"Sorting {len(combined_items_data)} combined items by publication date (newest first)...")
    combined_items_data.sort(key=lambda x: x['pub_date'], reverse=True) # Sort by datetime objects

    items_added_to_xml = 0
    for item_data in combined_items_data[:MAX_FEED_ITEMS]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_data['title']
        ET.SubElement(item, "link").text = item_data['link']
        ET.SubElement(item, "description").text = item_data['description']
        # Format pubDate according to RFC 822 for RSS output
        ET.SubElement(item, "pubDate").text = item_data['pub_date'].strftime("%a, %d %b %Y %H:%M:%S %z") # Reverted to include time and timezone
        ET.SubElement(item, "guid", isPermaLink=str(item_data['is_permalink']).lower()).text = item_data['guid']
        items_added_to_xml +=1

    logging.info(f"Added {items_added_to_xml} total items to the feed XML.")

    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    try:
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding='utf-8')
    except Exception as parse_err:
        logging.warning(f"Could not prettify XML output using minidom. Error: {parse_err}. Saving raw XML.")
        pretty_xml_str = xml_str

    try:
        with open(filename, "wb") as f:
            f.write(pretty_xml_str)
        logging.info(f"RSS feed successfully generated and saved to {filename}")
    except IOError as e:
        logging.error(f"Error writing RSS feed file {filename}: {e}")


if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"Starting AUST notice scraping process...")
    logging.info(f"Local time: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')} (Timezone Offset: {LOCAL_TIMEZONE})")
    try:
        # 1. Fetch notices first
        fetched_notices = fetch_notices()

        # If fetching failed or returned no notices, we might still need to check if the file exists
        # but we primarily care about comparing fetched notices to existing ones.

        # 2. Load existing GUIDs
        current_guids = load_existing_feed_guids(RSS_FILENAME)

        # 3. Determine if there are new notices by comparing fetched GUIDs to existing ones
        new_notices_found = False
        if fetched_notices: # Check if fetching returned any notices
            for notice in fetched_notices:
                if notice['guid'] not in current_guids:
                    new_notices_found = True
                    logging.info(f"New notice found: GUID {notice['guid']} Title: {notice['title']}")
                    # No need to log all new ones here, just need to know if at least one exists
                    break 

        # 4. Generate feed ONLY if new notices were found
        if new_notices_found:
            logging.info("New notices detected based on GUID comparison. Generating updated RSS feed.")
            # Pass the already fetched notices and loaded GUIDs
            generate_rss_feed(fetched_notices, current_guids, RSS_FILENAME)
        else:
            # Log why we are skipping
            if not fetched_notices:
                 logging.info("No notices were fetched from the source URL.")
            else:
                 logging.info("No new notices found based on GUID comparison with the existing feed.")
            logging.info("RSS feed generation skipped.")

        end_time = datetime.now()
        logging.info(f"Process finished. Duration: {end_time - start_time}")
    except Exception as e:
        logging.error(f"Unexpected error during execution: {e}", exc_info=True)
        sys.exit(1)
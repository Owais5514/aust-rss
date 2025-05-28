#!/usr/bin/env python3
"""
Simple validation script to check if RSS feeds are properly formatted.
"""
import xml.etree.ElementTree as ET
import sys
import os

def validate_rss_feed(filename):
    """Validate an RSS feed file."""
    if not os.path.exists(filename):
        print(f"❌ {filename}: File does not exist")
        return False
    
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        
        # Check if it's a valid RSS structure
        if root.tag != 'rss':
            print(f"❌ {filename}: Root element is not 'rss'")
            return False
        
        channel = root.find('channel')
        if channel is None:
            print(f"❌ {filename}: No 'channel' element found")
            return False
        
        # Check required elements
        required_elements = ['title', 'link', 'description']
        for element in required_elements:
            if channel.find(element) is None:
                print(f"❌ {filename}: Missing required element '{element}'")
                return False
        
        # Count items
        items = channel.findall('item')
        print(f"✅ {filename}: Valid RSS feed with {len(items)} items")
        return True
        
    except ET.ParseError as e:
        print(f"❌ {filename}: XML parsing error - {e}")
        return False
    except Exception as e:
        print(f"❌ {filename}: Unexpected error - {e}")
        return False

def main():
    """Main validation function."""
    feeds_to_check = ['feed.xml', 'shed_scholarship_feed.xml']
    all_valid = True
    
    print("🔍 Validating RSS feeds...")
    
    for feed in feeds_to_check:
        is_valid = validate_rss_feed(feed)
        all_valid = all_valid and is_valid
    
    if all_valid:
        print("\n🎉 All RSS feeds are valid!")
        sys.exit(0)
    else:
        print("\n❌ Some RSS feeds have issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Health check script for the RSS generation workflow.
Checks if the RSS feeds have been updated recently and contain fresh content.
"""
import xml.etree.ElementTree as ET
import sys
import os
from datetime import datetime, timezone, timedelta

def check_feed_freshness(filename, max_age_hours=24):
    """Check if an RSS feed has been updated recently."""
    if not os.path.exists(filename):
        print(f"❌ {filename}: File does not exist")
        return False
    
    try:
        # Check file modification time
        file_mtime = os.path.getmtime(filename)
        file_time = datetime.fromtimestamp(file_mtime, timezone.utc)
        current_time = datetime.now(timezone.utc)
        age_hours = (current_time - file_time).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            print(f"⚠️  {filename}: Feed is {age_hours:.1f} hours old (max: {max_age_hours})")
            return False
        
        # Parse XML and check lastBuildDate
        tree = ET.parse(filename)
        root = tree.getroot()
        channel = root.find('channel')
        
        if channel is not None:
            last_build = channel.find('lastBuildDate')
            if last_build is not None and last_build.text:
                print(f"✅ {filename}: Last built at {last_build.text}")
            
            # Count items
            items = channel.findall('item')
            if len(items) == 0:
                print(f"⚠️  {filename}: No items found in feed")
                return False
            
            print(f"✅ {filename}: Contains {len(items)} items, age: {age_hours:.1f} hours")
            return True
        
        print(f"❌ {filename}: Invalid RSS structure")
        return False
        
    except Exception as e:
        print(f"❌ {filename}: Error checking feed - {e}")
        return False

def main():
    """Main health check function."""
    feeds_to_check = [
        ('feed.xml', 6),  # AUST feed should be updated every 3 hours, allow 6 hours
        ('shed_scholarship_feed.xml', 25)  # Scholarship feed less frequent, allow 25 hours
    ]
    
    all_healthy = True
    
    print("🏥 Running RSS feed health check...")
    print(f"⏰ Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    for feed_file, max_age in feeds_to_check:
        is_healthy = check_feed_freshness(feed_file, max_age)
        all_healthy = all_healthy and is_healthy
    
    if all_healthy:
        print("\n💚 All RSS feeds are healthy!")
        sys.exit(0)
    else:
        print("\n🔴 Some RSS feeds need attention!")
        sys.exit(1)

if __name__ == "__main__":
    main()

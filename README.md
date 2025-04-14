# AUST Notice Board RSS Feed

An automated system that scrapes the Ahsanullah University of Science and Technology (AUST) notice board and converts it into an RSS feed.

## Overview

This project automatically checks the AUST notice board for new notices and generates an RSS feed that users can subscribe to. The system runs on a schedule optimized for Bangladesh time:

- 8 AM - 12 PM: Hourly checks
- 1 PM - 6 PM: Every 3 hours
- 7 PM - 12 AM: Hourly checks

## Features

- **Smart Content Checking**: Only processes when new content is detected
- **Content Hash Verification**: Uses MD5 hashing to avoid duplicates
- **Weekly Forced Refresh**: Ensures consistency with a full refresh once per week
- **Conditional HTTP Requests**: Uses If-Modified-Since headers when possible
- **Network Retry Logic**: Automatically retries in case of temporary network failures
- **Comprehensive Logging**: Maintains detailed logs of all operations

## Usage

To subscribe to the RSS feed, add the following URL to your RSS reader:

```
https://Owais5514.github.io/AUST-rss/feed.xml
```

## Technical Details

The system uses GitHub Actions to run automatically on schedule. The workflow:

1. Checks if there are new notices by comparing content hashes
2. If new content is detected, fetches and parses the notices
3. Generates an updated RSS feed file
4. Commits and pushes the changes to GitHub

## Maintenance

To make changes to the script:

1. Edit the `generate-rss.py` file
2. Update selectors in the configuration section if the website structure changes
3. Commit and push your changes

## Debugging

Check the GitHub Actions logs for real-time execution details, or review the `rss_generator.log` file in the repository for historic execution logs.

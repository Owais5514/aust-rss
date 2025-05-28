# AUST RSS Feed Generator

An automated system that scrapes the Ahsanullah University of Science and Technology (AUST) notice board and Bangladesh Ministry of Education scholarship announcements, converting them into RSS feeds.

## Overview

This project automatically checks multiple sources for new notices and generates RSS feeds that users can subscribe to. The system runs automatically every 3 hours using GitHub Actions with improved error handling and reliability.

## Features

- **Dual Feed Generation**: 
  - AUST university notices
  - Bangladesh MoE scholarship announcements
- **Smart Content Checking**: Only processes when new content is detected
- **Content Hash Verification**: Uses MD5 hashing to avoid duplicates
- **Robust Error Handling**: Network retries, timeout handling, and graceful failures
- **Feed Validation**: Automatic validation of generated RSS feeds
- **Health Monitoring**: Periodic health checks to ensure feeds are fresh
- **Comprehensive Logging**: Maintains detailed logs of all operations
- **Improved Git Operations**: Better handling of concurrent updates and conflicts

## RSS Feed URLs

Subscribe to these feeds in your RSS reader:

**AUST University Notices:**
```
https://Owais5514.github.io/AUST-rss/feed.xml
```

**Bangladesh MoE Scholarship Notices:**
```
https://Owais5514.github.io/AUST-rss/shed_scholarship_feed.xml
```

## Recent Improvements (GitHub Actions Fixes)

The following issues have been identified and fixed:

### 1. **Dependency Management**
- **Issue**: Manual package installation instead of using `requirements.txt`
- **Fix**: Now uses `pip install -r requirements.txt` with dependency caching

### 2. **Git Conflict Resolution**
- **Issue**: Race conditions when multiple jobs try to commit simultaneously
- **Fix**: Consolidated into single job with proper git pull/rebase logic

### 3. **Error Handling**
- **Issue**: Scripts would fail silently on network errors
- **Fix**: Added retry logic, timeout handling, and graceful error recovery

### 4. **Feed Validation**
- **Issue**: No validation of generated RSS feeds
- **Fix**: Added automatic feed validation step

### 5. **Resource Optimization**
- **Issue**: Redundant dependency installations and missing caching
- **Fix**: Added pip caching and optimized workflow structure

### 6. **Monitoring & Health Checks**
- **Issue**: No way to monitor feed freshness and health
- **Fix**: Added separate health check workflow and validation scripts

## Workflow Structure

### Main Generation Workflow (every 3 hours)
1. **Setup**: Python environment with cached dependencies
2. **Generation**: Both RSS feeds are generated with error handling
3. **Validation**: Feeds are validated for proper XML structure
4. **Commit**: Smart git operations with conflict resolution
5. **Push**: Retry logic for reliable updates

### Health Check Workflow (every hour)
1. **Monitoring**: Checks feed freshness and content quality
2. **Reporting**: Creates workflow summaries for easy monitoring
3. **Alerting**: Non-blocking checks that don't interfere with main workflow

## Files & Scripts

- `generate-rss.py` - Main AUST notice scraper with comprehensive logging
- `generate-shed-scholarship-rss.py` - Bangladesh scholarship scraper with retry logic
- `validate_feeds.py` - RSS feed validation utility
- `health_check.py` - Feed health monitoring script
- `requirements.txt` - Python dependencies
- `.github/workflows/main.yml` - Main RSS generation workflow
- `.github/workflows/health-check.yml` - Health monitoring workflow

## Troubleshooting

If the RSS feeds are not updating:

1. **Check GitHub Actions**: Look for failed workflows in the Actions tab
2. **Review Logs**: Check `rss_generator.log` for detailed error information
3. **Manual Trigger**: Use "Run workflow" button in GitHub Actions
4. **Health Check**: Review health check workflow results

Common issues and solutions:
- **Network timeouts**: Scripts have automatic retry logic
- **Git conflicts**: Workflow includes conflict resolution
- **Invalid feeds**: Validation step catches malformed RSS
- **Stale content**: Health checks monitor feed freshness

## Development

To modify or extend the system:

1. **Local Testing**: Test scripts locally before committing
2. **Selector Updates**: Update CSS selectors if website structure changes
3. **Configuration**: Modify timing, retry counts, or feed limits as needed
4. **New Sources**: Add additional RSS feeds following existing patterns

## Maintenance

The system is designed to be self-maintaining with:
- Automatic error recovery
- Comprehensive logging
- Health monitoring
- Conflict resolution
- Feed validation

Regular maintenance tasks:
- Monitor workflow execution
- Review error logs if issues persist
- Update selectors if source websites change
- Adjust timing if needed based on source update patterns

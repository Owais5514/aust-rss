# COPILOT INSTRUCTIONS FOR AUST-RSS PROJECT

## Project Overview
This project scrapes the Ahsanullah University of Science and Technology (AUST) notice board and generates an RSS feed. The system uses GitHub Actions to run on a schedule optimized for Bangladesh time (UTC+6).

## User Preferences

### Code Style
- Use Python logging instead of print statements for all output
- Implement robust error handling with try/except blocks
- Add detailed comments for complex logic
- Use consistent function and variable naming (snake_case)

### Schedule Preferences
- Run hourly from 8 AM to 12 PM Bangladesh time (2-6 UTC)
- Run hourly from 7 PM to 12 AM Bangladesh time (13-18 UTC)
- Run every 3 hours in between (at 9,12 UTC)

### Performance Optimization
- Always check for new content before processing (using content hash comparison)
- Implement retry logic for network operations (3 attempts with increasing delay)
- Use conditional HTTP requests with If-Modified-Since when possible
- Perform a forced full refresh once per week regardless of detected changes

### Error Handling
- Log all errors with appropriate severity levels
- For critical errors, exit with non-zero status code
- Include stack traces for unexpected exceptions
- Implement graceful degradation when possible

### Documentation
- Maintain clear, up-to-date documentation in README.md
- Document any changes to the scheduling logic
- Keep requirements.txt updated with exact versions used

### Testing Suggestions
- Test against website structure changes
- Verify RSS feed validity against standard
- Test network error handling

## System Architecture
1. GitHub Actions workflow runs on schedule
2. Python script checks for new content using hash comparison
3. If new content detected, script scrapes notices
4. Script generates RSS feed XML
5. GitHub Actions commits and pushes changes

## File Purposes
- generate-rss.py: Main script for scraping and RSS generation
- requirements.txt: Python dependencies
- README.md: Project documentation
- .github/workflows/main.yml: GitHub Actions workflow definition
- feed.xml: Generated RSS feed output
- notice_cache.json: Cache for content hash and last-modified headers
- rss_generator.log: Log file for script operations

## Maintenance Tasks
- Update selectors if AUST website changes
- Check GitHub Actions logs for execution issues
- Review log file for warning/error patterns
- Periodically verify RSS feed is valid using a validator

## Future Enhancement Ideas
- Simple HTML interface for GitHub Pages
- Email notifications for critical errors
- Unit tests for scraper components

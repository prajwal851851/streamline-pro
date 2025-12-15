# Streaming Link Management System

This document describes the comprehensive streaming link management system that implements on-demand scraping, link health monitoring, and automatic cleanup.

## Overview

The system follows a three-step strategy to ensure users always have fresh, working streaming links:

1. **On-Demand Scraping**: Scrape links when users request movies, ensuring freshness
2. **Link Health Monitoring**: Periodically check if links are still active
3. **Multiple Sources** (Future): Aggregate links from multiple streaming sites

## Step 1: On-Demand Scraping

### How It Works

When a user requests a movie (e.g., visits `/streaming/123/`):

1. Django API checks the database for existing active links
2. If no active links found OR all links are stale (>24 hours old), it triggers on-demand scraping
3. Scrapy spider runs in the background to fetch fresh links for that specific movie
4. New links are saved to the database automatically

### Implementation

- **Django View**: `streaming/views.py` - `StreamingMovieViewSet.retrieve()` method
- **Scraper Utility**: `streaming/scraper_utils.py` - `scrape_movie_on_demand()` function
- **Spider Support**: `scraper/spiders/example_spider.py` - accepts `target_url` parameter

### Manual Refresh

Users can manually trigger a refresh:
- **API Endpoint**: `POST /api/streaming/movies/{id}/refresh_links/`
- **Frontend**: "Refresh Links" button on movie detail page

## Step 2: Link Health Monitoring

### Management Command

Run periodically (e.g., every hour via cron):

```bash
python manage.py check_link_health
```

### Options

- `--limit N`: Check only first N links (useful for testing)
- `--older-than N`: Only check links older than N hours
- `--timeout N`: Request timeout in seconds (default: 5)

### Examples

```bash
# Check all links
python manage.py check_link_health

# Check only first 100 links
python manage.py check_link_health --limit 100

# Only check links older than 24 hours
python manage.py check_link_health --older-than 24
```

### What It Does

1. Sends HEAD requests to all streaming links
2. Marks links as `is_active=False` if they return:
   - 404 Not Found
   - 403 Forbidden
   - 410 Gone
   - Timeout errors
   - Other errors
3. Updates `last_checked` timestamp
4. Automatically deletes movies with no active links

## Step 3: Frontend Filtering

### Active Links Only

- **Serializer**: `MovieSerializer.get_links()` only returns `is_active=True` links
- **Frontend**: Automatically filters out inactive links
- **UI**: Shows "Active" or "Inactive" badge for each link

### Refresh Button

Users can manually refresh links:
- Click "Refresh Links" button on movie detail page
- Triggers on-demand scraping
- Page refreshes after 3 seconds to show new links

## Database Models

### Movie Model
- `imdb_id`: Unique identifier (used as slug)
- `title`, `year`, `type`, `poster_url`, `synopsis`

### StreamingLink Model
- `movie`: Foreign key to Movie
- `source_url`: The streaming URL
- `is_active`: Boolean flag (True = link works, False = dead)
- `last_checked`: Timestamp of last health check
- `quality`, `language`: Metadata

## Cron Job Setup

To run health checks automatically, add to crontab:

```bash
# Check links every hour
0 * * * * cd /path/to/project/MovieBackend && /path/to/venv/bin/python manage.py check_link_health

# Or on Windows Task Scheduler:
# Program: C:\path\to\venv\Scripts\python.exe
# Arguments: manage.py check_link_health
# Start in: C:\path\to\project\MovieBackend
```

## Cleanup Script

Run `cleanup_dead_links.py` to remove movies with no links:

```bash
python cleanup_dead_links.py
```

This script:
- Removes movies with no streaming links
- Removes movies with only dead/inactive links
- Shows statistics before and after cleanup

## API Endpoints

### List Movies
- `GET /api/streaming/movies/` - List all movies
- `GET /api/streaming/movies/?type=movie` - Filter by type
- `GET /api/streaming/movies/?type=show` - Filter by type

### Get Movie Detail
- `GET /api/streaming/movies/{id}/` - Get movie with active links only
  - Automatically triggers scraping if no active links found

### Refresh Links
- `POST /api/streaming/movies/{id}/refresh_links/` - Manually trigger scraping

## Future: Multiple Sources (Step 3)

To implement multiple source aggregation:

1. Create additional spiders for other sites (Fmovies, Prmovies, LookMovie, etc.)
2. All spiders use IMDB ID as the universal key
3. Store links from all sources under the same Movie object
4. Frontend can prioritize "best" links but show all available options

## Troubleshooting

### Links Not Updating
- Check if Scrapy is running: `ps aux | grep scrapy`
- Check Django logs for scraping errors
- Verify `scraper_utils.py` paths are correct

### Health Check Not Working
- Verify `requests` library is installed: `pip install requests`
- Check network connectivity
- Review management command logs

### Frontend Not Showing Links
- Verify serializer is filtering correctly
- Check browser console for API errors
- Ensure `is_active=True` links exist in database


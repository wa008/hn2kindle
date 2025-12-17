# HN2Kindle

Daily Hacker News digest delivered to your Kindle.

## What it does

- Fetches yesterday's top HN stories (stable/fixed content)
- Extracts article content with headings preserved
- Converts to EPUB format
- Sends to your Kindle via email

## Deploy with GitHub Actions (Recommended - Free)

Deploy once and get daily digests automatically. GitHub Actions is **completely free** for public repos and has generous free tier for private repos.

Add these secrets to your repo (Settings → Secrets → Actions):
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD` ([create here](https://myaccount.google.com/apppasswords))
- `KINDLE_EMAILS` (single or multiple comma-separated)

## Run locally

1. **Clone and install:**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Configure `.env`:**
   ```
   TOP_POSTS_COUNT=50
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   KINDLE_EMAILS=you@kindle.com
   ```

3. **Run locally:**
   ```bash
   cd src && python3 main.py --skip-send --keep-epub
   ```

## CLI Options
For easy testing: 
```
--skip-send    Skip sending to Kindle
--keep-epub    Keep the EPUB file
--count N      Number of posts to fetch
--output PATH  Custom output path
```

## Free join
1. Add "hackernews2kindle@gmail.com" to your Kindle email list
2. Tell me your Kindle email address
3. I will add you to the list
# Job Board Scraper

A high-performance, scalable job board scraping system designed to collect and process job postings from multiple sources with enterprise-grade reliability.

---

## 🌟 Features

- **Multi-Source Scraping:** Extract job data from various job boards with configurable selectors.
- **Flexible Input:** Accept URLs from CSV, TXT, or Excel files.
- **Intelligent Deduplication:** Prevent duplicate entries using composite key hashing.
- **Continuous Operation:** Schedule scraping at configurable intervals (default: every 2 hours).
- **Large-Scale Ready:** Optimized for handling 1M+ job records efficiently.
- **Multiple Rendering Engines:** Supports BeautifulSoup, Selenium, and Playwright for different complexity levels.
- **Comprehensive Data Extraction:** Captures 12+ data points per job posting.
- **Production Deployment:** Ready for deployment on AWS EC2, DigitalOcean, Heroku, Docker, and other platforms.

---

## 📋 Data Collected

For each job posting, the system extracts:

- Job Title
- Company Name
- Location
- Work Setting (remote/in-person/hybrid)
- Job Type (full-time, part-time, contract, etc.)
- Company Logo URL
- Job Description
- Requirements/Years of Experience
- Application URL
- Date Posted
- Date Collected
- Source URL

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser (for Selenium/Playwright)
- 4GB+ RAM recommended for large-scale scraping

### Installation

Clone and setup:

```sh
git clone <repository-url>
cd job-board-scraper
```

Install dependencies:

```sh
pip install -r requirements.txt
```

Install browser drivers (if using Selenium/Playwright):

```sh
# Playwright browsers
python -m playwright install

# Or for Selenium (alternative)
# Download ChromeDriver from https://chromedriver.chromium.org/
# Place it in your PATH
```

Add URLs to scrape:  
Edit `data/input_urls.csv` or `data/testdata.txt` with your target job board URLs.

Run a test scrape:

```sh
python -m src.main --once
```

---

## 📁 Project Structure

```
job-board-scraper/
├── data/
│   ├── jobs.csv                 # Output file with all scraped jobs
│   ├── jobs.json                # Output file (JSON format)
│   ├── input_urls.csv           # Input URLs to scrape
│   └── testdata.txt             # Additional test URLs
├── logs/
│   └── scraper.log              # Automated logging output
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration settings
│   ├── deduplicator.py          # Duplicate detection and prevention
│   ├── main.py                  # Entry point and CLI interface
│   ├── parser.py                # HTML parsing and data extraction
│   ├── scheduler.py             # Automated scheduling system
│   ├── scraper.py               # Core scraping functionality
│   ├── storage.py               # Output storage management (CSV, JSON, Excel)
│   └── utils.py                 # Helper functions and utilities
├── Dockerfile                   # Containerization configuration
├── requirements.txt             # Python dependencies
├── run.sh                       # Convenience execution script
└── README.md                    # Project documentation
```

---

## ⚙️ Configuration

Modify [`src/config.py`](src/config.py) to customize scraper behavior:

```python
SCRAPING_INTERVAL_HOURS = 2
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 30  # seconds
OUTPUT_FORMATS = ['csv', 'json', 'excel']
```

Add custom job board selectors in `JOB_BOARD_SELECTORS`.

---

## 🎯 Usage

### Single Run

```sh
python -m src.main --once
```

### Scheduled Operation

```sh
python -m src.main --schedule
# Custom interval (every 4 hours)
python -m src.main --schedule --interval 4
```

### Using Helper Script

```sh
chmod +x run.sh
./run.sh --once
./run.sh --schedule --interval 2
```

### Docker Deployment

Build and run:

```sh
docker build -t job-scraper .
docker run -d \
  --name job-scraper \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  job-scraper
```

---

## 🧪 Testing

Run validation checks:

```sh
python -c "from src.utils import read_input_file; print(read_input_file('data/input_urls.csv'))"
python -c "from src.parser import HTMLParser; p = HTMLParser(); print(p.parse_job_page('<html>...</html>', 'http://test.com'))"
```

---

## 📝 Logs and Monitoring

Logs are stored in `logs/scraper.log` with different detail levels:

- INFO: Scraping progress and statistics
- WARNING: Retries and minor issues
- ERROR: Failures requiring attention

Monitor logs with:

```sh
tail -f logs/scraper.log
```

---

## 🔧 Customization

- Add new job boards: Update patterns in [`src/parser.py`](src/parser.py) and selectors in [`src/config.py`](src/config.py).
- Custom output format: Extend [`src/storage.py`](src/storage.py).
- Rate limiting: Adjust `CONCURRENT_REQUESTS` and delays in [`src/config.py`](src/config.py).

---

## 📊 Performance Optimization

- Enable Playwright: Set `use_playwright=True` in [`src/scraper.py`](src/scraper.py).
- Increase concurrency: Adjust `CONCURRENT_REQUESTS` in config.
- Database backend: Consider modifying [`src/storage.py`](src/storage.py) to use PostgreSQL/MySQL.
- Distributed scraping: Run multiple instances with different URL batches.

---

## 🤝 Contributing

- Fork the repository
- Create a feature branch: `git checkout -b feature-name`
- Make changes and test thoroughly
- Submit a pull request with description

---

## ⚠️ Legal Considerations

- Respect robots.txt files
- Add delays between requests to avoid overwhelming servers
- Check terms of service for target websites
- Consider using official APIs when available

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🆘 Support

For issues and questions:

- Check logs in `logs/scraper.log`
- Verify input URLs format
- Ensure all dependencies are installed
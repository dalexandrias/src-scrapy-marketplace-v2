# Scrapy settings for olx_marketplace project

BOT_NAME = "olx_marketplace"

SPIDER_MODULES = ["olx_marketplace.spiders"]
NEWSPIDER_MODULE = "olx_marketplace.spiders"

# User agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 4

# Configure a delay for requests
DOWNLOAD_DELAY = 2

# Disable cookies
COOKIES_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "olx_marketplace.pipelines.OlxPipeline": 300,
}

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable showing throttling stats
AUTOTHROTTLE_DEBUG = False

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Logging
LOG_LEVEL = "INFO"
LOG_ENCODING = "utf-8"

# Request fingerprinter
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Feed export encoding
FEED_EXPORT_ENCODING = "utf-8"

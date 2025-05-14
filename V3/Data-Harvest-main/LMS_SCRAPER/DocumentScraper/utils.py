import re #functions for URL extraction.

URL_PATTERN = re.compile(r'\b(?:https?://|www\.)[^\s<>]+')

def clean_urls(urls):
    unique_urls = set()
    for url in urls:
        if url:
            processed_url = url.lower().strip()
            if processed_url:
                unique_urls.add(processed_url)
    return sorted(list(unique_urls))
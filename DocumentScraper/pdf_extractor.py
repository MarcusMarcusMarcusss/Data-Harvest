# Contains the function to extract URLs from PDF files.
import fitz  # PyMuPDF
import os
# Import items from utils.py
from utils import URL_PATTERN, clean_urls

def extract_urls_from_pdf(filepath):
    urls = []
    try:
        with fitz.open(filepath) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extraction of hyperlink objects
                page_links = page.get_links() # Returns a list of dictionaries
                for link in page_links:
                    # Use .get() for safety in case keys are missing
                    if link.get('kind') == fitz.LINK_URI:
                        urls.append(link.get('uri', ''))

                #Extract urls in plain text using regex specified in utils.py
                text = page.get_text("text")
                urls.extend(URL_PATTERN.findall(text))
    except Exception as e:
        print(f"--> Error processing PDF file '{os.path.basename(filepath)}': {e}")
        return [] # Return empty list on error

    return clean_urls(urls)


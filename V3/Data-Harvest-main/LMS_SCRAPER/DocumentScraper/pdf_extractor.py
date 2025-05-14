# Contains the function to extract URLs from PDF files.
import fitz
import os
from .utils import clean_urls

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

    except Exception as e:
        print(f"--> Error processing PDF file '{os.path.basename(filepath)}': {e}")
        return []

    return clean_urls(urls)


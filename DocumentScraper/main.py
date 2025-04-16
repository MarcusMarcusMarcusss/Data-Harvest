import os
import sys

from docx_extractor import extract_urls_from_docx
from pdf_extractor import extract_urls_from_pdf
from pptx_extractor import extract_urls_from_pptx
from excel_extractor import extract_urls_from_excel

DIRECTORY_TO_SCAN = 'C:\\Users\\Saugat\\Documents\\Test'

def main():
    all_extracted_data = {}
    processed_files_count = 0
    supported_extensions = ('.docx', '.pdf', '.pptx', '.xlsx')

    print(f"Scanning directory: '{DIRECTORY_TO_SCAN}' for {', '.join(supported_extensions)} files...")

    #Check if the directory exists
    if not os.path.isdir(DIRECTORY_TO_SCAN):
        print(f"Error: Directory not found or is not a valid directory: '{DIRECTORY_TO_SCAN}'")
        return

    # Iterate through all documents/files in the directory
    for filename in os.listdir(DIRECTORY_TO_SCAN):
        full_path = os.path.join(DIRECTORY_TO_SCAN, filename)
        file_lower = filename.lower()

        if os.path.isfile(full_path):
            extracted_links = None
            file_processed = False

            if file_lower.endswith('.docx'):
                print(f"\nProcessing DOCX: {filename} ")
                extracted_links = extract_urls_from_docx(full_path)
                file_processed = True
            elif file_lower.endswith('.pdf'):
                print(f"\nProcessing PDF: {filename} ")
                extracted_links = extract_urls_from_pdf(full_path)
                file_processed = True
            elif file_lower.endswith('.pptx'):
                print(f"\nProcessing PPTX: {filename} ")
                extracted_links = extract_urls_from_pptx(full_path)
                file_processed = True
            elif file_lower.endswith('.xlsx'): #
                print(f"\nProcessing XLSX: {filename} ")
                extracted_links = extract_urls_from_excel(full_path)
                file_processed = True

            if file_processed:
                processed_files_count += 1
                if extracted_links:
                     print(f"Found {len(extracted_links)} unique URLs:")
                     all_extracted_data[filename] = extracted_links
                     # Print links found in this file
                     for i, link in enumerate(extracted_links):
                         print(f"  {i + 1}. {link}")
                else:
                     # Only print if the file was actually processed
                     print("No URLs found or extracted from this file.")
                     all_extracted_data[filename] = []

    print("\n")
    print("Scan Complete.")
    print(f"Processed {processed_files_count} relevant file(s) ({', '.join(supported_extensions)}).")

if __name__ == "__main__":
    try:
        import docx
        import fitz
        import pptx
        import openpyxl
    except ImportError as e:
        print(f"Error: Missing required library - {e.__class__.__name__} ('{e.name}')")
        print("Please ensure required libraries are installed:")
        print("  pip install python-docx PyMuPDF python-pptx openpyxl")

    main()
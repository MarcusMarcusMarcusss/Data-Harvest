import requests
import time
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
import os
import requests

def download_file(session, file_URL, save_directory="downloads"):
    try:
        response = session.get(file_URL, stream=True)

        print(f"Status Code: {response.status_code}")
        content_type = response.headers.get("Content-Type", "")
        print(f"Content-Type: {content_type}")

        if "text/html" in content_type:
            print("The response is HTML, not a downloadable file.")
            print(response.text[:500])
            return None

        if response.status_code == 200:
            file_name = get_file_name(response, file_URL)

            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            file_path = os.path.join(save_directory, file_name)

            if file_exists_and_same_size(file_path, response):
                return file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            # Save the file
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1000):
                    file.write(chunk)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"File downloaded and saved as: {os.path.basename(file_path)} at {timestamp}")
            return os.path.basename(file_path), timestamp
        else:
            print(f"Failed to download file. Status: {response.status_code}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_file_name(response, url):
    content_disposition = response.headers.get('Content-Disposition', '')
    if 'filename=' in content_disposition:
        file_name = content_disposition.split('filename=')[1].strip('"')
    else:
        file_name = urlsplit(url).path.split('/')[-1] or "downloaded_file"
    return file_name

def file_exists_and_same_size(file_path, response):
    if os.path.exists(file_path):
        existing_size = os.path.getsize(file_path)
        remote_size = int(response.headers.get('Content-Length', 0))
        if existing_size == remote_size:
            print(f"The file {os.path.basename(file_path)} already exists with same size.Skip download.")
            return True
        else:
            print(f"The file {os.path.basename(file_path)} exists but different sizes.Downloading again.")
            return False
    return False

def detect_file_type_from_content(file_name):
    try:
        if not file_name or '.' not in file_name:
            return 'unknown'
        
        file_extension = file_name.rsplit('.', 1)[-1].lower()
        
        extension_map = {
            'pdf': 'pdf',
            'pptx': 'presentation',
            'docx': 'document',
        }
        return extension_map.get(file_extension, 'unknown')
    
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return None
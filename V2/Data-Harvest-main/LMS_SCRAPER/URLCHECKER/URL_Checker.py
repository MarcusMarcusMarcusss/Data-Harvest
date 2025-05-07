# LMS_SCRAPER/URLCHECKER/URL_Checker.py
import requests
import base64
import json
import os
import time

VT_API_KEY = "adcafb9cd4413cb8b4a0dcf2986b76a4747322ba13ab27e4ada298adf799e8eb"
# ---

# Public API allows ~4 requests per minute. Be cautious.
API_DELAY_SECONDS = 16 # Delay in seconds between API calls

def check_url_virustotal(url_to_check):

    api_key = VT_API_KEY
    result = {'url': url_to_check, 'status': 'error', 'message': 'Initialization error'} # Default result

    # Check if the hardcoded key is still the placeholder
    if not api_key or api_key == "YourActualApiKeyGoesHere":
        result['message'] = 'VirusTotal API key not configured (still placeholder).'
        return result

    # VT API v3 uses URL identifier derived from the URL itself
    try:
        # Ensure URL is properly encoded for the API ID generation
        url_bytes = url_to_check.encode('utf-8')
        url_id = base64.urlsafe_b64encode(url_bytes).rstrip(b'=').decode('utf-8')
    except Exception as e:
         result['message'] = f'Error encoding URL: {e}'
         return result

    vt_url_report_endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
    headers = {"accept": "application/json", "x-apikey": api_key}

    try:
        # Make the GET request to VirusTotal API
        response = requests.get(vt_url_report_endpoint, headers=headers, timeout=30) # Added timeout
    except requests.exceptions.Timeout:
        result['message'] = 'Network timeout connecting to VirusTotal API.'
        return result
    except requests.exceptions.RequestException as e:
         result['message'] = f'Network error connecting to VirusTotal API: {e}'
         return result

    # Process the response based on status code
    if response.status_code == 200:
        try:
            response_data = response.json()
            # Extract relevant attributes and stats
            attributes = response_data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            result['status'] = 'ok'
            result['stats'] = stats # e.g., {'malicious': 0, 'suspicious': 0, ...}
            result['message'] = 'Analysis retrieved successfully.'
        except json.JSONDecodeError:
             result['status'] = 'error'
             result['message'] = 'Failed to decode API response (JSON).'
        except Exception as e:
             result['status'] = 'error'
             result['message'] = f'Error processing API response: {e}'

    elif response.status_code == 404:
        result['status'] = 'not_found'
        result['message'] = 'URL not found in VirusTotal database (never scanned).'
    elif response.status_code == 401:
        result['status'] = 'error'
        result['message'] = 'API Error: Authentication failed (Invalid API Key?).'
    elif response.status_code == 429:
        result['status'] = 'error'
        result['message'] = 'API Error: Rate limit exceeded.'
    else:
        # Catch other potential API errors
        result['status'] = 'error'
        result['message'] = f'API Error: Status Code {response.status_code}. Response: {response.text[:100]}' # Include start of response text

    return result

def get_api_delay():
    """Returns the configured API delay."""
    return API_DELAY_SECONDS

if __name__ == "__main__":
    test_url = "http://www.google.com"
    print(f"Checking example URL: {test_url}")

    # Check if API key is configured before proceeding
    if not VT_API_KEY or VT_API_KEY == "YourActualApiKeyGoesHere":
        print("ERROR: VirusTotal API Key not set in the script. Please replace the placeholder.")
    else:
        report = check_url_virustotal(test_url)
        print("\n--- VirusTotal Report ---")
        print(f"URL: {report.get('url')}")
        print(f"Status: {report.get('status')}")
        if report.get('status') == 'ok':
            print(f"Stats: {report.get('stats')}")
        else:
            print(f"Message: {report.get('message')}")


import requests
import base64
import json
import os
import time
import whois
from urllib.parse import urlparse
from datetime import datetime

VT_API_KEY = "adcafb9cd4413cb8b4a0dcf2986b76a4747322ba13ab27e4ada298adf799e8eb"
API_DELAY_SECONDS = 16 # Delay in seconds between API calls

def get_domain_creation_date(url_string):
   #Extracts the domain from a URL and attempts to find its creation date via WHOIS.

    if not url_string:
        return None
    try:
        parsed_url = urlparse(url_string)
        domain = parsed_url.hostname

        if not domain:
            return None

        w = whois.whois(domain)

        # Check if whois result itself is None or doesn't have creation_date
        if not w or not hasattr(w, 'creation_date') or w.creation_date is None:
            return None

        creation_date = w.creation_date
        if isinstance(creation_date, list):
            # Take the first date if it's a list (some WHOIS records might return multiple)
            creation_date = creation_date[0] if creation_date else None

        if isinstance(creation_date, datetime):
            return creation_date.strftime('%Y-%m-%d')
        else:
            return None
    except whois.parser.PywhoisError as e:
        return None
    except Exception as e:
        return None

def check_url_virustotal(url_to_check):
    #Checks single URL against the VirusTotal API v3.

    api_key = VT_API_KEY
    result = {'url': url_to_check, 'status': 'error', 'message': 'Initialization error'}

    if not api_key or api_key == "YourActualApiKeyGoesHere": # Added check for default placeholder
        result['message'] = 'VirusTotal API key not configured (still placeholder).'
        return result

    try:
        url_bytes = url_to_check.encode('utf-8')
        url_id = base64.urlsafe_b64encode(url_bytes).rstrip(b'=').decode('utf-8')
    except Exception as e:
         result['message'] = f'Error encoding URL: {e}'
         return result

    vt_url_report_endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
    headers = {"accept": "application/json", "x-apikey": api_key}

    try:
        response = requests.get(vt_url_report_endpoint, headers=headers, timeout=30)
    except requests.exceptions.Timeout:
        result['message'] = 'Network timeout connecting to VirusTotal API.'
        return result
    except requests.exceptions.RequestException as e:
         result['message'] = f'Network error connecting to VirusTotal API: {e}'
         return result

    if response.status_code == 200:
        try:
            response_data = response.json()
            attributes = response_data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            result['status'] = 'ok'
            result['stats'] = stats
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
        result['status'] = 'error'
        result['message'] = f'API Error: Status Code {response.status_code}. Response: {response.text[:100]}'
    return result

def get_api_delay():
    """Returns the configured API delay."""
    return API_DELAY_SECONDS

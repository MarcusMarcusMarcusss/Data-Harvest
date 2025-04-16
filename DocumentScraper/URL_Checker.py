import json
import base64
import time
import os
import sys

INPUT_FILENAME = "test.txt"

VT_API_KEY = os.environ.get('VIRUSTOTAL_API_KEY', "adcafb9cd4413cb8b4a0dcf2986b76a4747322ba13ab27e4ada298adf799e8eb")

API_DELAY_SECONDS = 16

def check_url_virustotal(url_to_check, api_key):
    if not api_key or api_key == "YOUR_VIRUSTOTAL_API_KEY":
        return {'status': 'error', 'message': 'VirusTotal API key not configured.'}
    try:
        url_bytes = url_to_check.encode('utf-8')
        url_id = base64.urlsafe_b64encode(url_bytes).rstrip(b'=').decode('utf-8')
    except Exception as e:
         return {'status': 'error', 'message': f'Error encoding URL: {e}'}

    vt_url_report_endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
    headers = {"accept": "application/json", "x-apikey": api_key}
    result = {'url': url_to_check}

    try:
        response = requests.get(vt_url_report_endpoint, headers=headers)
    except requests.exceptions.RequestException as e:
         return {'status': 'error', 'message': f'Network error: {e}'}

    if response.status_code == 200:
        try:
            response_data = response.json()
            attributes = response_data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            result['status'] = 'ok'
            result['stats'] = stats
        except json.JSONDecodeError:
             result['status'] = 'error'
             result['message'] = 'Failed to decode API response (JSON).'

    elif response.status_code == 404:
        result['status'] = 'not_found'
        result['message'] = 'URL not found in VirusTotal database.'
    else:
        result['status'] = 'error'
        result['message'] = f'API Error: Status Code {response.status_code}'

    return result

def run_checker():
    print(f"Reading URLs from: {INPUT_FILENAME}")
    if not VT_API_KEY or VT_API_KEY == "YOUR_VIRUSTOTAL_API_KEY":
        print("\nERROR: VirusTotal API Key not configured.")
        sys.exit(1)
    try:
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            urls_to_process = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"\nERROR: Input file not found: {INPUT_FILENAME}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Failed to read input file {INPUT_FILENAME}: {e}")
        sys.exit(1)

    if not urls_to_process:
        print("No URLs found in the input file.")
        sys.exit(0)

    print(f"Found {len(urls_to_process)} URLs to check.")
    print("-" * 30)

    for index, url in enumerate(urls_to_process):
        if index > 0:
            print(f"\nWaiting {API_DELAY_SECONDS}s for VT rate limit...")
            time.sleep(API_DELAY_SECONDS)

        print(f"\nChecking URL {index + 1}/{len(urls_to_process)}: {url}")
        report = check_url_virustotal(url, VT_API_KEY)

        print(f"  Status: {report.get('status', 'N/A')}")
        if report['status'] == 'ok':
            stats = report.get('stats', {})
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            undetected = stats.get('undetected', 0)
            total_engines = malicious + suspicious + harmless + undetected
            print(f"  Result: Malicious={malicious}, Suspicious={suspicious}, Harmless={harmless}, Undetected={undetected} (of {total_engines} engines)")
        else:
            print(f"  Message: {report.get('message', 'No details')}")

        if report['status'] == 'error' and 'Rate limit exceeded' in report.get('message', ''):
             print("\nERROR: Rate limit hit. Stopping further checks.")
             break

    print("URL Checking Complete.")


if __name__ == "__main__":
    import requests
    run_checker()

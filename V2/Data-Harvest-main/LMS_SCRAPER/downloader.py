import os
import re
import unicodedata
from urllib.parse import urlparse, unquote

import requests


def clean_filename(filename):
    if not isinstance(filename, str):
        filename = str(filename)  # Ensure it's a string
    try:
        filename = re.sub(r'[^\x00-\x7F]+', '', filename)
        filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    except Exception as e:
        pass
    filename = re.sub(r'[\\/*?:"<>|\x00-\x1F\x7F]', "", filename)
    filename = re.sub(r'\s+', '_', filename).strip('._')
    parts = filename.split('.')
    if len(parts) > 2:
        filename = parts[0] + '.' + parts[-1]
    elif len(parts) == 2:
        filename = parts[0] + '.' + parts[1]
    else:  # No dot
        filename = parts[0]

    filename = re.sub(r'\.+', '.', filename)
    reserved_names = re.compile(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$', re.IGNORECASE)
    if reserved_names.match(filename.split('.')[0]):
        filename = "_" + filename
    max_len = 200
    if len(filename) > max_len:
        name_part, dot, extension = filename.rpartition('.')
        if dot and len(extension) < 15:
            allowed_name_len = max_len - len(extension) - 1
            if allowed_name_len < 1:
                filename = filename[:max_len]
            else:
                name_part = name_part[:allowed_name_len]
                filename = f"{name_part}.{extension}"
        else:
            filename = filename[:max_len]
    if not filename or filename.strip('.') == "":
        filename = "downloaded_file"
    return filename


def download_file(session, file_url, save_dir, fallback_name="downloaded_file", request_timeout=30):
    local_filepath = None
    downloaded_bytes = 0
    print(f"Attempting download request for: {file_url}")

    try:
        # Make the request
        response = session.get(file_url, stream=True, timeout=request_timeout, allow_redirects=True)
        response.raise_for_status()
        print(f"Download successful")

        moodle_name_base = None
        moodle_name_ext = ""
        real_ext = ""

        cleaned_fallback = clean_filename(fallback_name) if fallback_name else ""

        if cleaned_fallback and cleaned_fallback != "downloaded_file" and cleaned_fallback != "Unknown_File":
            base, dot, ext = cleaned_fallback.rpartition('.')
            if dot and len(ext) <= 5 and len(ext) > 0:
                moodle_name_base = base
                moodle_name_ext = dot + ext
            else:
                moodle_name_base = cleaned_fallback
                moodle_name_ext = ""
        else:
            moodle_name_base = None

        if not moodle_name_base:
            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                filename_match = re.search(r'filename\*=(?:UTF-8\'\')?([^;]+)', content_disposition, re.IGNORECASE) \
                                 or re.search(r'filename="([^"]+)"', content_disposition)
                if filename_match:
                    potential_name = filename_match.group(1).strip('" ')
                    header_filename = unquote(potential_name)
                    base, dot, ext_part = header_filename.rpartition('.')
                    if not dot:
                        moodle_name_base = header_filename
                        moodle_name_ext = ""
                    else:
                        moodle_name_base = base
                        moodle_name_ext = dot + ext_part

            if not moodle_name_base:
                try:
                    final_url_path = urlparse(response.url).path
                    if final_url_path and final_url_path != '/':
                        potential_name = os.path.basename(unquote(final_url_path))
                        base, dot, ext_part = potential_name.rpartition('.')
                        if not dot:
                            moodle_name_base = potential_name
                            moodle_name_ext = ""
                        else:
                            moodle_name_base = base
                            moodle_name_ext = dot + ext_part
                except Exception:
                    pass

        if not moodle_name_base:
            moodle_name_base = "downloaded_file"

        if not moodle_name_ext:
            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                filename_match = re.search(r'filename\*=(?:UTF-8\'\')?([^;]+)', content_disposition, re.IGNORECASE) \
                                 or re.search(r'filename="([^"]+)"', content_disposition)
                if filename_match:
                    potential_name = filename_match.group(1).strip('" ')
                    header_filename = unquote(potential_name)
                    _, dot, ext_part = header_filename.rpartition('.')
                    if dot: real_ext = dot + ext_part

            if not real_ext:
                try:
                    final_url_path = urlparse(response.url).path
                    if final_url_path and final_url_path != '/':
                        potential_name = os.path.basename(unquote(final_url_path))
                        _, dot, ext_part = potential_name.rpartition('.')
                        if dot: real_ext = dot + ext_part
                except Exception:
                    pass

        final_filename = moodle_name_base + (moodle_name_ext if moodle_name_ext else real_ext)
        cleaned_filename = clean_filename(final_filename)
        local_filepath = os.path.join(save_dir, cleaned_filename)

        if os.path.exists(local_filepath):
            print(f"file already exists: {local_filepath}")
            return local_filepath

        if not os.path.isdir(save_dir):
            try:
                os.makedirs(save_dir, exist_ok=True)
                print(f"Created directory: {save_dir}")
            except OSError as e:
                print(f"ERROR creating directory '{save_dir}': {e}")
                return None

        print(f"Downloading to: {local_filepath}")
        try:
            with open(local_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
            print(f"Download complete ({downloaded_bytes} bytes)")
            return local_filepath
        except IOError as e:
            print(f"ERROR writing file '{local_filepath}': {e}")
            if os.path.exists(local_filepath) and downloaded_bytes == 0:
                try:
                    os.remove(local_filepath)
                except OSError:
                    pass
            return None


    except (requests.exceptions.RequestException, ConnectionError, requests.exceptions.Timeout,
            requests.exceptions.HTTPError) as e:
        print(f"ERROR during download request/stream for {file_url}: {e}")
        if local_filepath and os.path.exists(local_filepath) and downloaded_bytes == 0:
            try:
                os.remove(local_filepath)
            except OSError:
                pass
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during download of {file_url}: {e}")
        if local_filepath and os.path.exists(local_filepath) and downloaded_bytes == 0:
            try:
                os.remove(local_filepath)
            except OSError:
                pass
        return None

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def find_activity_instances(soup_or_tag, activity_type_class=None):
    if not soup_or_tag:
        return []
    instances = []
    selector = 'li.activity'
    if activity_type_class:
        selector += f'.{activity_type_class}'
    try:
        instances = soup_or_tag.find_all('li', class_=lambda x: x and 'activity' in x.split() and (
                    not activity_type_class or activity_type_class in x.split()))
        if not instances:
            instances = soup_or_tag.find_all('div', class_='activityinstance')
            if activity_type_class and instances:
                instances = [inst for inst in instances if f'modtype_{activity_type_class}' in inst.get('class', [])]
        if not instances and activity_type_class:
            instances = soup_or_tag.find_all('li', attrs={'data-type': activity_type_class})
    except Exception as e:
        pass
    return instances


def is_external(url, base_url):
    if not url:
        return False
    try:
        target_parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        if not target_parsed.scheme in ['http', 'https'] or not target_parsed.netloc:
            return False
        return base_parsed.netloc != target_parsed.netloc
    except ValueError:
        return False


def extract_all_external_links(soup_or_tag, page_url, source_description="Unknown"):
    external_links_dict = {}
    if not soup_or_tag:
        return external_links_dict

    try:
        base_url_parsed = urlparse(page_url)
    except ValueError:
        return external_links_dict

    try:
        anchor_tags = soup_or_tag.find_all("a", href=True)
    except Exception as e:
        return external_links_dict

    for tag in anchor_tags:
        href = tag.get('href')
        if not href or href.startswith('#') or href.lower().startswith('javascript:') or href.lower().startswith(
                'mailto:'):
            continue
        try:
            absolute_url = urljoin(page_url, href)
            if is_external(absolute_url, page_url):
                if absolute_url not in external_links_dict:
                    external_links_dict[absolute_url] = source_description
        except ValueError:
            continue
        except Exception as e:
            continue
    return external_links_dict


def extract_potential_file_links(soup_or_tag, page_url, source_description="Unknown"):
    file_links_dict = {}
    if not soup_or_tag:
        return file_links_dict

    try:
        potential_links = soup_or_tag.find_all(
            'a',
            href=re.compile(r'/pluginfile\.php/|/mod/resource/view\.php|/mod/assign/|/mod/folder/view\.php')
        )
    except Exception as e:
        return file_links_dict

    for tag in potential_links:
        href = tag.get('href')
        if not href or href.startswith('#') or href.lower().startswith('javascript:'):
            continue
        try:
            absolute_url = urljoin(page_url, href)
            if absolute_url not in file_links_dict:
                file_links_dict[absolute_url] = source_description
        except ValueError:
            continue
        except Exception as e:
            continue
    return file_links_dict


def extract_url_type_links(soup_or_tag, base_url):
    found_url_items = []
    processed_urls = set()
    activity_instances = find_activity_instances(soup_or_tag, 'url')
    for instance in activity_instances:
        link_tag = instance.find("a", href=True)
        if not link_tag: continue
        href = link_tag.get("href")
        if not href or href.startswith('#') or href.lower().startswith('javascript:'): continue
        full_url = urljoin(base_url, href)
        if '/mod/url/view.php' not in full_url: continue
        instancename_span = instance.find('span', class_='instancename')
        if not instancename_span: continue
        name = instancename_span.get_text(strip=True)
        accesshide_span = instancename_span.find('span', class_='accesshide')
        if accesshide_span and accesshide_span.get_text(strip=True) in name:
            name = name.replace(accesshide_span.get_text(strip=True), '').strip()
        if not name: name = instancename_span.contents[
            0].strip() if instancename_span.contents else "Unknown URL Resource"
        if full_url not in processed_urls:
            found_url_items.append((name, full_url))
            processed_urls.add(full_url)
    return found_url_items


def extract_page_links(soup_or_tag, base_url):
    found_urls = set()
    activity_instances = find_activity_instances(soup_or_tag, 'page')
    for instance in activity_instances:
        link_tag = instance.find("a", href=True)
        if not link_tag: continue
        href = link_tag.get("href")
        if not href or href.startswith(('#', 'javascript:')): continue
        full_url = urljoin(base_url, href)
        if '/mod/page/view.php' not in full_url: continue
        found_urls.add(full_url)
    return found_urls


def extract_forum_links(soup_or_tag, base_url):
    forum_links = []
    processed_urls = set()
    activity_instances = find_activity_instances(soup_or_tag, 'forum')
    for instance in activity_instances:
        link_tag = instance.find("a", href=True)
        if not link_tag: continue
        href = link_tag.get("href")
        if not href or href.startswith('#') or href.lower().startswith('javascript:'): continue
        full_url = urljoin(base_url, href)
        if '/mod/forum/view.php' not in full_url: continue
        instancename_span = instance.find('span', class_='instancename')
        if not instancename_span: continue
        forum_name = instancename_span.get_text(strip=True)
        accesshide_span = instance.find('span', class_='accesshide')
        if accesshide_span and accesshide_span.get_text(strip=True) in forum_name:
            forum_name = forum_name.replace(accesshide_span.get_text(strip=True), '').strip()
        if not forum_name: forum_name = instancename_span.contents[
            0].strip() if instancename_span.contents else "Unknown Forum"
        if full_url not in processed_urls:
            forum_links.append((forum_name, full_url))
            processed_urls.add(full_url)
    if not forum_links:
        try:
            for link in soup_or_tag.find_all("a", class_="aalink", href=True):
                span = link.find("span", class_="accesshide")
                if span and "Forum" in span.get_text(strip=True):
                    forum_name_tag = link.find("span", class_="instancename")
                    if forum_name_tag:
                        href = link.get("href")
                        if href and not href.startswith('#') and '/mod/forum/view.php' in href:
                            full_url_fallback = urljoin(base_url, href)
                            if full_url_fallback not in processed_urls:
                                forum_name_fallback = forum_name_tag.get_text(strip=True)
                                forum_name_fallback = forum_name_fallback.replace(span.get_text(strip=True), '').strip()
                                if not forum_name_fallback: forum_name_fallback = forum_name_tag.contents[
                                    0].strip() if forum_name_tag.contents else "Unknown Forum"
                                forum_links.append((forum_name_fallback, full_url_fallback))
                                processed_urls.add(full_url_fallback)
        except Exception as e:
            pass
    return forum_links


def extract_file_links(soup_or_tag, base_url):
    found_file_items = []
    processed_urls = set()
    activity_instances = find_activity_instances(soup_or_tag, 'resource') \
                         + find_activity_instances(soup_or_tag, 'folder') \
                         + find_activity_instances(soup_or_tag, 'assign')

    for instance in activity_instances:
        link_tag = instance.find("a", href=True)
        if not link_tag: continue
        href = link_tag.get("href")
        if not href or href.startswith('#') or href.lower().startswith('javascript:'): continue
        full_url = urljoin(base_url, href)
        is_potential_file = False
        if '/mod/resource/view.php' in full_url:
            is_potential_file = True
        elif '/mod/folder/view.php' in full_url:
            is_potential_file = True
        elif '/mod/assign/view.php' in full_url:
            is_potential_file = True
        elif '/pluginfile.php/' in full_url:
            is_potential_file = True
        if not is_potential_file: continue
        instancename_span = instance.find('span', class_='instancename')
        if not instancename_span: continue
        name = instancename_span.get_text(strip=True)
        accesshide_span = instancename_span.find('span', class_='accesshide')
        if accesshide_span and accesshide_span.get_text(strip=True) in name:
            name = name.replace(accesshide_span.get_text(strip=True), '').strip()
        if not name: name = instancename_span.contents[
            0].strip() if instancename_span.contents else "Unknown File/Folder"
        if full_url not in processed_urls:
            found_file_items.append((name, full_url))
            processed_urls.add(full_url)
    return found_file_items


def extract_external_url(url_resource_page_url, session):
    target_urls = []
    try:
        response = session.get(url_resource_page_url, timeout=20, allow_redirects=True)
        response.raise_for_status()
        final_url = response.url
        if is_external(final_url, url_resource_page_url):
            target_urls.append(final_url)
            return target_urls
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find("div", role="main") \
                      or soup.find("div", id="region-main") \
                      or soup.find("div", id="page-content") \
                      or soup.find("div", class_="urlworkaround") \
                      or soup.find("div", class_="box generalbox url") \
                      or soup
        link_tag = None
        if content_div:
            link_container = content_div.find('div', class_='urlworkaround') or content_div.find('div',
                                                                                                 class_='box generalbox url')
            if link_container:
                link_tag = link_container.find('a', href=True)
            if not link_tag:
                link_tag = content_div.find('a', href=True)
        if link_tag and link_tag.get('href'):
            href = link_tag['href']
            abs_href = urljoin(url_resource_page_url, href)
            if is_external(abs_href, url_resource_page_url):
                target_urls.append(abs_href)
        return target_urls
    except requests.exceptions.Timeout:
        return []
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []


def extract_links_from_page(page_url, session):
    source_description = f"Page: {page_url}"
    external_links_dict = {}
    file_links_dict = {}
    try:
        response = session.get(page_url, timeout=20)
        response.raise_for_status()
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return ({}, {})
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find(attrs={"role": "main"}) \
                       or soup.find("div", id="page-content") \
                       or soup.find('div', class_='box generalbox page-content') \
                       or soup.find("div", id="region-main") \
                       or soup
        if not main_content:
            main_content = soup

        external_links_dict = extract_all_external_links(main_content, page_url, source_description)
        file_links_dict = extract_potential_file_links(main_content, page_url, source_description)

        return (external_links_dict, file_links_dict)

    except requests.exceptions.Timeout:
        return ({}, {})
    except requests.exceptions.RequestException as e:
        return ({}, {})
    except Exception as e:
        return ({}, {})


def extract_forum_discussions(forum_url, session):
    discussions = []
    processed_disc_urls = set()
    try:
        response = session.get(forum_url, timeout=20)
        response.raise_for_status()
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", role="main") \
                       or soup.find("div", id="region-main") \
                       or soup
        if not main_content:
            return []
        discussion_table = main_content.find("table", class_="discussion-list")
        if discussion_table:
            rows = discussion_table.find_all('tr', class_=lambda x: x and 'discussion' in x.split())
            if not rows: rows = discussion_table.find_all('tr')
            for row in rows:
                link_cell = row.find('th', class_='topic') or row.find('td', class_='topic')
                if link_cell:
                    link_tag = link_cell.find('a', href=lambda x: x and 'discuss.php' in x)
                    if link_tag:
                        href = link_tag.get('href')
                        title = link_tag.get_text(strip=True) or "Unknown Discussion"
                        abs_discussion_url = urljoin(forum_url, href)
                        if abs_discussion_url not in processed_disc_urls:
                            discussions.append((title, abs_discussion_url))
                            processed_disc_urls.add(abs_discussion_url)
        if not discussions:
            direct_links = main_content.find_all('a', class_='w-100 h-100 d-block',
                                                 href=lambda x: x and 'discuss.php' in x) \
                           + main_content.find_all('a', class_='discussion-title',
                                                   href=lambda x: x and 'discuss.php' in x) \
                           + main_content.find_all('a', href=lambda x: x and '/mod/forum/discuss.php' in x)
            unique_links = {link.get('href'): link for link in direct_links}.values()
            if unique_links:
                for link_tag in unique_links:
                    href = link_tag.get('href')
                    if not href: continue
                    title = link_tag.get('aria-label') or link_tag.get('title') or link_tag.get_text(
                        strip=True) or "Unknown Discussion"
                    abs_discussion_url = urljoin(forum_url, href)
                    if abs_discussion_url not in processed_disc_urls:
                        discussions.append((title, abs_discussion_url))
                        processed_disc_urls.add(abs_discussion_url)
        return discussions
    except requests.exceptions.Timeout:
        return []
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []


def extract_links_from_discussion(discussion_url, session, discussion_title=""):
    source_description = f"Discussion: '{discussion_title}' ({discussion_url})"
    external_links_dict = {}
    file_links_dict = {}
    try:
        response = session.get(discussion_url, timeout=25)
        response.raise_for_status()
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return ({}, {})
        discussion_soup = BeautifulSoup(response.text, "html.parser")
        main_content = discussion_soup.find("div", role="main") \
                       or discussion_soup.find("div", id="region-main") \
                       or discussion_soup
        if not main_content:
            return ({}, {})
        posts = main_content.find_all('div', id=re.compile(r'^post-content-\d+')) \
                + main_content.find_all("article", attrs={"data-region": "post"}) \
                + main_content.find_all('div', class_=re.compile(r'\bforumpost\b'))
        if not posts:
            posts = [main_content]
        for post_area in posts:
            content_div = post_area.find('div', class_='posting-content') \
                          or post_area.find('div', class_='text_to_html') \
                          or post_area.find('div', class_='post-content-container') \
                          or post_area.find('div', class_='post-content') \
                          or post_area
            if content_div:
                external_links_dict.update(extract_all_external_links(content_div, discussion_url, source_description))
                file_links_dict.update(extract_potential_file_links(content_div, discussion_url, source_description))

        return (external_links_dict, file_links_dict)

    except requests.exceptions.Timeout:
        return ({}, {})
    except requests.exceptions.RequestException as e:
        return ({}, {})
    except Exception as e:
        return ({}, {})

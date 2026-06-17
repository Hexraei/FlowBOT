import urllib.request
import urllib.parse
from html.parser import HTMLParser
import os
import re
import csv
import time

class LinkExtractor(HTMLParser):
    """Parses HTML and extracts all anchor links."""
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    # Resolve relative URLs
                    absolute_url = urllib.parse.urljoin(self.base_url, value)
                    # Strip fragment identifiers
                    absolute_url = urllib.parse.urlsplit(absolute_url)._replace(fragment="").geturl()
                    self.links.add(absolute_url)

class MLStripper(HTMLParser):
    """Strips HTML tags to extract plain text."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False

    def handle_data(self, d):
        if not self.in_script and not self.in_style:
            self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def clean_text(text):
    # Normalize multiple newlines and spaces
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def get_page_name(url):
    path = urllib.parse.urlparse(url).path
    if not path or path == '/':
        return "homepage"
    filename = os.path.basename(path)
    if not filename:
        return "index"
    return os.path.splitext(filename)[0]

def fetch_with_retry(url, headers, retries=3, delay=1.5):
    """Fetches a URL with retries on connection timeout."""
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')
                return 200, html, ""
        except Exception as e:
            print(f"  Attempt {attempt} failed to fetch {url}: {e}")
            if attempt == retries:
                # Get status code if HTTPError
                status_code = getattr(e, "code", 500)
                return status_code, "", str(e)
            time.sleep(delay * attempt)
    return 500, "", "Unknown failure"

def main():
    start_url = "https://flowzint.in/"
    domain_filter = "flowzint.in"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    kb_dir = r"d:\SupportBOT\knowledge_base"
    os.makedirs(kb_dir, exist_ok=True)
    
    to_visit = [start_url]
    visited = set()
    
    csv_rows = []
    
    print("Starting recursive link discovery crawler...")
    
    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
            
        visited.add(url)
        name = get_page_name(url)
        print(f"Crawling ({len(visited)}): {name} -> {url}...")
        
        status, html, err_msg = fetch_with_retry(url, headers)
        
        success = (status == 200)
        char_count = 0
        contains_price = False
        
        if success and html:
            # 1. Parse links to continue discovery
            link_extractor = LinkExtractor(url)
            try:
                link_extractor.feed(html)
                for link in link_extractor.links:
                    parsed_link = urllib.parse.urlparse(link)
                    # Only follow links on same domain and within .html files (or directory index)
                    if domain_filter in parsed_link.netloc:
                        if parsed_link.path.endswith('.html') or parsed_link.path == '' or parsed_link.path == '/':
                            if link not in visited and link not in to_visit:
                                to_visit.append(link)
            except Exception as e:
                print(f"  Warning: failed to extract links from {url}: {e}")
                
            # 2. Extract Title
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else name.replace("-", " ").title()
            
            # 3. Extract text content
            stripper = MLStripper()
            try:
                stripper.feed(html)
                raw_text = stripper.get_data()
                cleaned_text = clean_text(raw_text)
                char_count = len(cleaned_text)
                
                # Check for pricing information
                # Look for ₹, Rs, INR, 1999, 999, etc.
                contains_price = bool(re.search(r'₹|Rs\.|INR|1999|999', cleaned_text, re.IGNORECASE))
                
                # Write to knowledge base
                output_content = f"Title: {title}\nURL: {url}\n\n{cleaned_text}"
                file_path = os.path.join(kb_dir, f"{name}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(output_content)
                print(f"  Saved to {file_path} (Chars: {char_count}, Has Price: {contains_price})")
                
            except Exception as e:
                success = False
                err_msg = f"Parsing failed: {e}"
                print(f"  Error parsing text: {e}")
        else:
            print(f"  Failed to fetch: {err_msg}")
            
        csv_rows.append({
            "page_name": name,
            "url": url,
            "http_status": status,
            "scrape_success": success,
            "char_count": char_count,
            "contains_price": contains_price,
            "error_message": err_msg
        })
        
    # Write status sheet to CSV
    csv_path = r"d:\SupportBOT\scrape_status.csv"
    print(f"\nWriting audit results to {csv_path}...")
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["page_name", "url", "http_status", "scrape_success", "char_count", "contains_price", "error_message"])
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"Audit status report successfully saved! Total unique pages crawled: {len(visited)}")
    except Exception as e:
        print(f"Failed to write CSV log: {e}")

if __name__ == "__main__":
    main()

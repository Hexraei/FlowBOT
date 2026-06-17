import sys
import os
from playwright.sync_api import sync_playwright

def main():
    url = "https://flowzint.in/fz/internships.html"
    scraped_file = r"d:\SupportBOT\knowledge_base\internships.txt"
    
    print("Starting Playwright validation...")
    
    # 1. Start Playwright and fetch live page content
    try:
        with sync_playwright() as p:
            print("Launching headless Chromium browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"Loading {url} in browser...")
            page.goto(url, timeout=30000)
            
            # Wait for content to render
            page.wait_for_timeout(2000)
            
            print("Extracting visible text from page body...")
            browser_text = page.locator("body").inner_text()
            
            browser.close()
    except Exception as e:
        print(f"Playwright Execution Failed: {e}")
        sys.exit(1)
        
    print("\n" + "="*50)
    print("Playwright Live Browser Scan Results:")
    print("="*50)
    
    # Check for price presence in browser text
    browser_has_price = "1999" in browser_text
    browser_has_pass = "Complete Access Pass" in browser_text
    
    print(f"Contains '1999'              : {browser_has_price}")
    print(f"Contains 'Complete Access Pass': {browser_has_pass}")
    
    if not (browser_has_price and browser_has_pass):
        print("Error: Expected pricing details were not found on the live browser viewport!")
        sys.exit(1)
        
    # 2. Read our crawler's output text file
    if not os.path.exists(scraped_file):
        print(f"Error: Scraped output file not found at {scraped_file}")
        sys.exit(1)
        
    with open(scraped_file, "r", encoding="utf-8") as f:
        crawler_text = f.read()
        
    crawler_has_price = "1999" in crawler_text
    crawler_has_pass = "Complete Access Pass" in crawler_text
    
    print("\n" + "="*50)
    print("Crawler Output File Scan Results:")
    print("="*50)
    print(f"Contains '1999'              : {crawler_has_price}")
    print(f"Contains 'Complete Access Pass': {crawler_has_pass}")
    
    # Compare matching occurrences
    print("\n" + "="*50)
    print("Validation Summary:")
    print("="*50)
    
    if crawler_has_price and crawler_has_pass:
        print("Success: Pricing details successfully verified in both browser render and crawler output!")
    else:
        print("Failure: Pricing details are missing from our crawler output file.")
        sys.exit(1)
        
    # Check what else was in the old vs new response
    old_size = 1396
    new_size = os.path.getsize(scraped_file)
    print(f"Old internships.txt size: {old_size} bytes")
    print(f"New internships.txt size: {new_size} bytes")
    print(f"Additional data recovered: {new_size - old_size} bytes")
    print("Scrape verification completed successfully!")

if __name__ == "__main__":
    main()

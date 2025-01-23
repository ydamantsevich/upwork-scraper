from playwright.sync_api import sync_playwright
import time
import random


def scrape_job_details(link, cookies=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        context = browser.new_context()
        page = context.new_page()

        # Set cookies if provided
        if cookies:
            context.add_cookies(cookies)

        # Small pause before loading the page
        time.sleep(random.uniform(1.0, 2.0))

        try:
            response = page.goto(f"https://www.upwork.com{link}")
            
            if response.status != 200:
                print(f"Warning: Page returned status code {response.status}")
                
            # Check for CAPTCHA or other blocking elements
            if page.query_selector("div[class*='captcha']") or page.query_selector("div[class*='security-check']"):
                print("Warning: Detected possible CAPTCHA or security check page")
                page.screenshot(path="captcha_details_screenshot.png")
                print("Screenshot saved as captcha_details_screenshot.png")
                raise Exception("Security check or CAPTCHA detected")
                
            # Wait for page to load with increased timeout
            print("Waiting for job details to load...")
            page.wait_for_selector(".job-details-card .flex-1", timeout=60000)  # Increase timeout to 60 seconds
            time.sleep(random.uniform(1.0, 2.0))
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            browser.close()
            raise

        # Collect data
        title_element = page.query_selector(".job-details-card .flex-1")
        description_element = page.query_selector("p.text-body-sm")
        country_element = page.query_selector(
            ".cfe-ui-job-about-client li:nth-of-type(1) strong"
        )
        location_details_element = page.query_selector(
            ".cfe-ui-job-about-client li:nth-of-type(1) span:first-child"
        )

        # Check for elements and extract text
        title = title_element.inner_text() if title_element else "Title not found"
        description = (
            description_element.inner_text()
            if description_element
            else "Description not found"
        )
        country = (
            country_element.inner_text() if country_element else "Country not found"
        )
        location_details = (
            location_details_element.inner_text() if location_details_element else ""
        )

        # Form location string
        if location_details:
            location = f"{country} + {location_details}"
        else:
            location = country

        browser.close()
        return title, description, location


if __name__ == "__main__":
    job_link = "/some-job-link"  # Example job link
    title, description, location = scrape_job_details(job_link)
    print(f"Title: {title}\nDescription: {description}\nLocation: {location}")

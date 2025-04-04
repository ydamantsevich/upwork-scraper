from playwright.sync_api import sync_playwright
import time
import random
from datetime import datetime


def scrape_parent_job_links(cookies=None):
    """Scrapes initial job listing links"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ],
        )
        context = browser.new_context()
        page = context.new_page()

        try:
            if cookies:
                context.add_cookies(cookies)

            time.sleep(random.uniform(1.0, 2.0))

            response = page.goto(
                "https://www.upwork.com/nx/search/jobs/?amount=5000-&category2_uid=531770282580668418&hourly_rate=50-&location=Europe,Northern%20America,Israel,United%20Kingdom&per_page=10&sort=recency&t=0,1"
            )

            if response.status != 200:
                print(f"Warning: Page returned status code {response.status}")

            if page.query_selector("div[class*='captcha']") or page.query_selector(
                "div[class*='security-check']"
            ):
                print("Warning: Detected possible CAPTCHA or security check page")
                page.screenshot(path="captcha_screenshot.png")
                print("Screenshot saved as captcha_screenshot.png")
                raise Exception("Security check or CAPTCHA detected")

            print("Waiting for job listings to load...")
            page.wait_for_selector(".air3-link", timeout=60000)
            time.sleep(random.uniform(1.0, 2.0))

            job_links = page.query_selector_all("a.air3-link")
            links = [link.get_attribute("href") for link in job_links]

            return links

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise
        finally:
            browser.close()


def get_parent_job_details(page, link):
    """Extract main job details from the page"""
    title_element = page.query_selector(".job-details-card .flex-1")
    description_element = page.query_selector("p.text-body-sm")
    country_element = page.query_selector(
        ".cfe-ui-job-about-client li:nth-of-type(1) strong"
    )
    location_details_element = page.query_selector(
        ".cfe-ui-job-about-client li:nth-of-type(1) span:first-child"
    )

    title = title_element.inner_text() if title_element else "Title not found"
    description = (
        description_element.inner_text()
        if description_element
        else "Description not found"
    )
    country = country_element.inner_text() if country_element else "Country not found"
    location_details = (
        location_details_element.inner_text() if location_details_element else ""
    )

    location = f"{country} + {location_details}" if location_details else country

    return title, description, location


def scrape_parent_job(link, cookies=None, max_retries=3):
    """Scrapes a single parent job and its in-progress links with retries"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ],
        )
        context = browser.new_context()
        page = context.new_page()

        try:
            if cookies:
                context.add_cookies(cookies)

            time.sleep(random.uniform(1.0, 2.0))

            for attempt in range(max_retries):
                try:
                    response = page.goto(f"https://www.upwork.com{link}")
                    if response.status != 200:
                        print(f"Warning: Page returned status code {response.status}")
                        continue

                    if page.query_selector(
                        "div[class*='captcha']"
                    ) or page.query_selector("div[class*='security-check']"):
                        print(
                            "Warning: Detected possible CAPTCHA or security check page"
                        )
                        page.screenshot(
                            path=f"captcha_details_screenshot_{attempt}.png"
                        )
                        print(
                            f"Screenshot saved as captcha_details_screenshot_{attempt}.png"
                        )
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(5.0, 10.0))
                            continue
                        raise Exception("Security check or CAPTCHA detected")

                    print("Waiting for job details to load...")
                    page.wait_for_selector(".job-details-card .flex-1", timeout=60000)
                    time.sleep(random.uniform(1.0, 2.0))

                    title, description, location = get_parent_job_details(page, link)

                    # Import here to avoid circular import
                    from in_progress_jobs import find_in_progress_links

                    # Find in-progress links with retries
                    in_progress_links = find_in_progress_links(page, max_retries=3)

                    job_data = {
                        "url": f"https://www.upwork.com{link}",
                        "title": title,
                        "description": description,
                        "location": location,
                        "timestamp": datetime.now().isoformat(),
                        "source": "upwork.com",
                        "in_progress_links": (
                            " ; ".join(in_progress_links) if in_progress_links else ""
                        ),
                        "in_progress_titles": "",
                        "in_progress_descriptions": "",
                    }

                    if in_progress_links:
                        print(f"Found {len(in_progress_links)} in-progress links")

                    return job_data

                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(5.0, 10.0))
                    else:
                        raise

        finally:
            browser.close()

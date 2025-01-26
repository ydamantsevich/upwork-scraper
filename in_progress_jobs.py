from playwright.sync_api import sync_playwright
import time
import random
import csv


def find_in_progress_links(page, max_retries=3):
    """Find in-progress job links with retries"""
    in_progress_links = []

    for attempt in range(max_retries):
        try:
            print("Looking for in-progress button...")
            in_progress_button = page.query_selector(".jobs-in-progress-title")

            if not in_progress_button:
                print("No in-progress button found")
                return []

            print("Found in-progress button, clicking...")
            in_progress_button.click()
            time.sleep(random.uniform(2.0, 3.0))  # Increased wait time

            # Wait for the in-progress section to load
            page.wait_for_selector(
                ".air3-card-section:first-child .js-job-link", timeout=30000
            )

            # Get all in-progress job elements
            print("Looking for in-progress jobs...")
            in_progress_jobs = page.query_selector_all(
                ".air3-card-section:first-child .js-job-link"
            )
            print(f"Found {len(in_progress_jobs)} in-progress jobs")

            for job in in_progress_jobs:
                url = job.get_attribute("href")
                if url and url not in in_progress_links:
                    in_progress_links.append(url)
                    print(f"Found in-progress link: {url}")

            # If we found links, break the retry loop
            if in_progress_links:
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3.0, 5.0))
                # Try clicking the button again
                try:
                    in_progress_button = page.query_selector(".jobs-in-progress-title")
                    if in_progress_button:
                        in_progress_button.click()
                except:
                    pass
            else:
                print("Max retries reached for finding in-progress links")

    return in_progress_links


def scrape_in_progress_job(url, cookies, max_retries=3):
    """Scrape details for a single in-progress job with retries"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
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

            for attempt in range(max_retries):
                try:
                    time.sleep(random.uniform(2.0, 3.0))
                    response = page.goto(f"https://www.upwork.com{url}")

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
                            path=f"captcha_progress_screenshot_{attempt}.png"
                        )
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(5.0, 10.0))
                            continue
                        raise Exception("Security check or CAPTCHA detected")

                    # Wait for title with increased timeout
                    title_element = page.wait_for_selector(
                        ".job-details-card .flex-1", timeout=30000
                    )
                    time.sleep(random.uniform(1.0, 2.0))

                    # Wait for description with separate timeout
                    description_element = page.wait_for_selector(
                        "p.text-body-sm", timeout=30000
                    )

                    title = (
                        title_element.inner_text()
                        if title_element
                        else "Title not found"
                    )
                    description = (
                        description_element.inner_text()
                        if description_element
                        else "Description not found"
                    )

                    if (
                        title != "Title not found"
                        and description != "Description not found"
                    ):
                        return title, description

                    print(
                        f"Attempt {attempt + 1}: Title or description not found, retrying..."
                    )
                    time.sleep(random.uniform(3.0, 5.0))

                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(5.0, 10.0))
                    else:
                        raise

            return "Title not found", "Description not found"

        finally:
            browser.close()


def update_csv_with_progress_data(parent_url, in_progress_links, csv_filename):
    """Updates the CSV file with in_progress_links for the parent job"""
    rows = []
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["url"] == parent_url:
                row["in_progress_links"] = (
                    "|".join(in_progress_links) if in_progress_links else ""
                )
            rows.append(row)

    with open(csv_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def update_csv_with_details(
    parent_url, in_progress_url, title, description, csv_filename
):
    """Updates the CSV with title and description for an in-progress job"""
    rows = []
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["url"] == parent_url:
                titles = (
                    row["in_progress_titles"].split(" ; ")
                    if row["in_progress_titles"]
                    else []
                )
                descriptions = (
                    row["in_progress_descriptions"].split(" ; ")
                    if row["in_progress_descriptions"]
                    else []
                )
                links = (
                    row["in_progress_links"].split(" ; ")
                    if row["in_progress_links"]
                    else []
                )

                try:
                    idx = links.index(in_progress_url)
                    while len(titles) <= idx:
                        titles.append("")
                    while len(descriptions) <= idx:
                        descriptions.append("")

                    titles[idx] = title
                    descriptions[idx] = description

                    row["in_progress_titles"] = "|".join(titles)
                    row["in_progress_descriptions"] = "|".join(descriptions)
                except ValueError:
                    print(
                        f"Link {in_progress_url} not found in parent job {parent_url}"
                    )
            rows.append(row)

    with open(csv_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

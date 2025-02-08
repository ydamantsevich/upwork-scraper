from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time
import random
import csv


def get_random_user_agent():
    """Generate a random modern user agent"""
    chrome_versions = ["119.0.0.0", "120.0.0.0", "121.0.0.0", "122.0.0.0"]
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64",
        "Windows NT 10.0; WOW64",
        "Macintosh; Intel Mac OS X 10_15",
        "X11; Ubuntu; Linux x86_64",
    ]
    return f"Mozilla/5.0 ({random.choice(platforms)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36"


def get_random_viewport():
    """Generate random viewport sizes that look natural"""
    common_widths = [1366, 1440, 1536, 1920, 2560]
    common_heights = [768, 900, 864, 1080, 1440]
    return {
        "width": random.choice(common_widths),
        "height": random.choice(common_heights),
    }


def simulate_human_behavior(page):
    """Simulate realistic human behavior"""
    # Random initial pause
    time.sleep(random.uniform(2.0, 4.0))

    # Random mouse movements
    for _ in range(random.randint(3, 7)):
        page.mouse.move(
            random.randint(100, page.viewport_size["width"] - 100),
            random.randint(100, page.viewport_size["height"] - 100),
            steps=random.randint(5, 10),
        )
        time.sleep(random.uniform(0.5, 1.5))

    # Random scrolling
    for _ in range(random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(300, 700))
        time.sleep(random.uniform(1.0, 2.0))

    # Move back up sometimes
    if random.random() > 0.5:
        page.mouse.wheel(0, random.randint(-400, -200))
        time.sleep(random.uniform(1.0, 2.0))


def find_in_progress_links(page, max_retries=3):
    """Find in-progress job links with retries"""
    in_progress_links = []

    for attempt in range(max_retries):
        try:
            print("Looking for in-progress button...")
            simulate_human_behavior(page)

            in_progress_button = page.query_selector(".jobs-in-progress-title")

            if not in_progress_button:
                print("No in-progress button found")
                return []

            print("Found in-progress button, clicking...")
            # Move mouse naturally to button before clicking
            button_box = in_progress_button.bounding_box()
            if button_box:
                page.mouse.move(
                    button_box["x"] + button_box["width"] / 2 + random.uniform(-5, 5),
                    button_box["y"] + button_box["height"] / 2 + random.uniform(-5, 5),
                    steps=random.randint(5, 10),
                )
                time.sleep(random.uniform(0.3, 0.7))

            in_progress_button.click()
            time.sleep(random.uniform(2.0, 3.0))

            # Wait for the in-progress section to load
            page.wait_for_selector(
                ".air3-card-section:first-child .js-job-link", timeout=30000
            )

            simulate_human_behavior(page)

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
                    time.sleep(random.uniform(2.0, 3.0))  # Add delay between collecting links

            if in_progress_links:
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(5.0, 8.0))
                try:
                    in_progress_button = page.query_selector(".jobs-in-progress-title")
                    if in_progress_button:
                        in_progress_button.click()
                except:
                    pass
            else:
                print("Max retries reached for finding in-progress links")

    return in_progress_links


def scrape_in_progress_job(url, cookies, browser=None, profile_manager=None, max_retries=3):
    """Scrape details for a single in-progress job with retries, reusing browser instance"""
    if not browser:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

    # Get profile from manager or generate random if no manager
    if profile_manager:
        profile = profile_manager.get_profile()
        context = browser.new_context(
            viewport=profile["viewport"],
            user_agent=profile["user_agent"],
            color_scheme=profile["color_scheme"],
            locale=profile["locale"],
            timezone_id=profile["timezone"],
            permissions=["geolocation"],
        )
    else:
        viewport = get_random_viewport()
        context = browser.new_context(
            viewport=viewport,
            user_agent=get_random_user_agent(),
            color_scheme="dark" if random.random() > 0.5 else "light",
            locale=random.choice(["en-US", "en-GB", "en-CA"]),
            timezone_id=random.choice(
                ["America/New_York", "Europe/London", "Europe/Berlin"]
            ),
            permissions=["geolocation"],
        )

    page = context.new_page()
    stealth_sync(page)

    # Add randomized headers
    page.set_extra_http_headers(
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": f"en-US,en;q={random.uniform(0.8, 0.9):.1f}",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
        }
    )

    try:
        if cookies:
            context.add_cookies(cookies)

        # Add extensive browser fingerprint evasion
        page.evaluate(
            """() => {
            const evasions = {
                webdriver: undefined,
                webGL: true,
                chrome: {
                    runtime: true,
                    webstore: true
                },
                permissions: {
                    query: true
                },
                navigator: {
                    languages: ['en-US', 'en']
                }
            };
            
            // WebDriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => evasions.webdriver
            });
            
            // WebGL
            if (evasions.webGL) {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Open Source Technology Center';
                    }
                    if (parameter === 37446) {
                        return 'Mesa DRI Intel(R) HD Graphics (SKL GT2)';
                    }
                    return getParameter.apply(this, arguments);
                };
            }
            
            // Chrome
            if (evasions.chrome) {
                window.chrome = {
                    runtime: {},
                    webstore: {}
                };
            }
            
            // Permissions
            if (evasions.permissions) {
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = parameters => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            }
        }"""
        )

        for attempt in range(max_retries):
            try:
                simulate_human_behavior(page)

                response = page.goto(
                    f"https://www.upwork.com{url}",
                    wait_until="networkidle",
                    timeout=60000,
                )

                if response.status != 200:
                    print(f"Warning: Page returned status code {response.status}")
                    page.screenshot(path=f"error_screenshot_{attempt}.png")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(15.0, 25.0))
                    continue

                if page.query_selector("div[class*='captcha']") or page.query_selector(
                    "div[class*='security-check']"
                ):
                    print("Warning: Detected possible CAPTCHA or security check page")
                    page.screenshot(path=f"captcha_progress_screenshot_{attempt}.png")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(20.0, 30.0))
                        continue
                    raise Exception("Security check or CAPTCHA detected")

                simulate_human_behavior(page)

                title_element = page.wait_for_selector(
                    ".job-details-card .flex-1", timeout=45000, state="visible"
                )

                description_element = page.wait_for_selector(
                    "p.text-body-sm", timeout=30000
                )

                title = (
                    title_element.inner_text() if title_element else "Title not found"
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
                time.sleep(random.uniform(8.0, 12.0))

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(15.0, 25.0))
                else:
                    raise

        return "Title not found", "Description not found"

    finally:
        page.close()
        if not browser:
            browser.close()


def update_csv_with_progress_data(parent_url, in_progress_links, csv_filename):
    """Updates the CSV file with in_progress_links for the parent job"""
    rows = []
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["url"] == parent_url:
                row["in_progress_links"] = (
                    " ; ".join(in_progress_links) if in_progress_links else ""
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
                    clean_links = [
                        link.replace("https://www.upwork.com", "") for link in links
                    ]
                    idx = clean_links.index(in_progress_url)
                    while len(titles) <= idx:
                        titles.append("")
                    while len(descriptions) <= idx:
                        descriptions.append("")

                    titles[idx] = title
                    descriptions[idx] = description

                    row["in_progress_titles"] = " ; ".join(titles)
                    row["in_progress_descriptions"] = " ; ".join(descriptions)
                except ValueError:
                    print(
                        f"Link {in_progress_url} not found in parent job {parent_url}"
                    )
            rows.append(row)

    with open(csv_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

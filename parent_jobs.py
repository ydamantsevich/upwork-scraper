from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time
import random
from datetime import datetime
from in_progress_jobs import (
    get_random_user_agent,
    get_random_viewport,
    simulate_human_behavior,
    find_in_progress_links,
)


def scrape_parent_job_links(cookies=None, profile_manager=None):
    """Scrapes initial job listing links"""
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
            profile = profile_manager.get_profile(is_new_parent_job=True)
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

            # Add browser fingerprint evasion
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

            time.sleep(random.uniform(3.0, 5.0))

            response = page.goto(
                "https://www.upwork.com/nx/search/jobs/?amount=1000-4999,5000-&category2_uid=531770282580668418&location=Northern%20America&per_page=10&sort=recency&t=0,1",
                wait_until="networkidle",
                timeout=60000,
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

            simulate_human_behavior(page)

            print("Waiting for job listings to load...")
            page.wait_for_selector(".air3-link", timeout=60000)
            time.sleep(random.uniform(2.0, 4.0))

            job_links = page.query_selector_all("a.air3-link")
            links = []
            for link in job_links:
                href = link.get_attribute("href")
                links.append(href)
                # Add random delay between collecting links
                time.sleep(random.uniform(2.0, 3.0))

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


def scrape_parent_job(link, cookies=None, profile_manager=None, max_retries=3):
    """Scrapes a single parent job and its in-progress links with retries"""
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
            profile = profile_manager.get_profile(is_new_parent_job=True)
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

            # Add browser fingerprint evasion
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

            time.sleep(random.uniform(3.0, 5.0))

            for attempt in range(max_retries):
                try:
                    response = page.goto(
                        f"https://www.upwork.com{link}",
                        wait_until="networkidle",
                        timeout=60000,
                    )

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
                            time.sleep(random.uniform(15.0, 25.0))
                            continue
                        raise Exception("Security check or CAPTCHA detected")

                    simulate_human_behavior(page)

                    print("Waiting for job details to load...")
                    page.wait_for_selector(".job-details-card .flex-1", timeout=60000)
                    time.sleep(random.uniform(2.0, 4.0))

                    title, description, location = get_parent_job_details(page, link)

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
                        time.sleep(random.uniform(15.0, 25.0))
                    else:
                        raise

        finally:
            browser.close()

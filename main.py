from parent_jobs import scrape_parent_job_links, scrape_parent_job
from in_progress_jobs import (
    find_in_progress_links,
    scrape_in_progress_job,
    update_csv_with_progress_data,
    update_csv_with_details,
)
from browser_profile_manager import BrowserProfileManager
import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
import time
import random
import sys
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()

def get_random_delay(min_delay, max_delay):
    """Get a random delay with some gaussian distribution"""
    # Use gaussian distribution for more natural timing
    mu = (min_delay + max_delay) / 2
    sigma = (max_delay - min_delay) / 6  # 99.7% of values within min/max
    delay = random.gauss(mu, sigma)
    # Ensure delay stays within bounds
    return max(min_delay, min(max_delay, delay))

def get_cookies():
    """Get cookies from JSON file or environment variables"""
    cookies = []
    required_cookie_names = {
        # Authentication
        "master_access_token",
        "oauth2_global_js_token",
        "user_uid",
        "XSRF-TOKEN",
        "spt",
        "console_user",
        
        # Cloudflare Protection
        "__cf_bm",
        "__cflb",
        "_cfuvid",
        "AWSALB",
        "AWSALBCORS"
    }

    # Try to load cookies from JSON file first
    try:
        json_files = [f for f in os.listdir() if f.endswith('.json') and 'upwork.com' in f]
        if json_files:
            latest_file = max(json_files, key=os.path.getctime)  # Get most recent file
            print(f"Loading cookies from {latest_file}")
            
            with open(latest_file, 'r') as f:
                json_cookies = json.load(f)
                
            # Extract required cookies from JSON
            for cookie in json_cookies:
                if cookie['name'] in required_cookie_names:
                    cookies.append({
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.upwork.com'),
                        'path': cookie.get('path', '/')
                    })
            
            # Verify all required cookies are present
            found_cookies = {cookie['name'] for cookie in cookies}
            if 'master_access_token' in found_cookies:
                print("Successfully loaded cookies from JSON file")
                return cookies
            else:
                print("JSON file missing critical cookies, falling back to environment variables")
                cookies = []  # Reset cookies to try env vars
                
    except Exception as e:
        print(f"Error loading cookies from JSON: {e}")
        print("Falling back to environment variables")

    # Fall back to environment variables if JSON loading failed
    env_cookie_mapping = {
        "master_access_token": "UPWORK_MASTER_TOKEN",
        "oauth2_global_js_token": "UPWORK_OAUTH_TOKEN",
        "user_uid": "UPWORK_USER_UID",
        "XSRF-TOKEN": "UPWORK_XSRF_TOKEN",
        "spt": "UPWORK_SPT",
        "console_user": "UPWORK_CONSOLE_USER",
        "__cf_bm": "UPWORK_CF_BM",
        "__cflb": "UPWORK_CFLB",
        "_cfuvid": "UPWORK_CFUVID",
        "AWSALB": "UPWORK_AWSALB",
        "AWSALBCORS": "UPWORK_AWSALBCORS"
    }

    # Load from environment variables
    for cookie_name, env_var in env_cookie_mapping.items():
        value = os.getenv(env_var)
        if value and value != "your_master_token_here":
            cookies.append({
                "name": cookie_name,
                "value": value,
                "domain": ".upwork.com",
                "path": "/"
            })

    # Verify master token presence
    if not any(c['name'] == 'master_access_token' for c in cookies):
        raise ValueError("master_access_token not found in JSON or environment variables")

    return cookies

def get_proxy():
    """Get proxy configuration from environment variables"""
    proxy_host = os.getenv('PROXY_HOST')
    proxy_port = os.getenv('PROXY_PORT')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    if all([proxy_host, proxy_port, proxy_username, proxy_password]):
        return {
            'server': f'http://{proxy_host}:{proxy_port}',
            'username': proxy_username,
            'password': proxy_password
        }
    return None

def save_to_csv(jobs_data):
    """Saves data to CSV file and returns the filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upwork_jobs_{timestamp}.csv"

    if jobs_data:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=jobs_data[0].keys())
            writer.writeheader()
            writer.writerows(jobs_data)
        print(f"\nData saved to file: {filename}")
        print(f"Total jobs saved: {len(jobs_data)}")
        return filename
    else:
        print("No data to save")
        return None

def process_in_progress_jobs(csv_filename):
    """Process in-progress jobs from CSV and update with details"""
    try:
        cookies = get_cookies()
        print("Cookies successfully loaded")
    except ValueError as e:
        print(f"Error loading cookies: {e}")
        return

    # Initialize profile manager with stability mode from env
    stability_mode = os.getenv("SESSION_STABILITY", "medium")
    profile_manager = BrowserProfileManager(stability_mode)
    print(f"Using {stability_mode} stability mode for browser profiles")

    print("\nProcessing in-progress jobs from CSV...")
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
                proxy=get_proxy()
            )

            for row in rows:
                if row["in_progress_links"]:
                    parent_url = row["url"]
                    in_progress_links = row["in_progress_links"].split(" ; ")
                    print(f"\nProcessing in-progress jobs for {parent_url}")

                    for i, link in enumerate(in_progress_links, 1):
                        if not link:
                            continue
                        print(f"Processing in-progress job {i}/{len(in_progress_links)}")

                        try:
                            # Get job details with retries and timeouts
                            title, description = scrape_in_progress_job(
                                link, cookies, browser
                            )
                            if (
                                title
                                and description
                                and title != "Title not found"
                                and description != "Description not found"
                            ):
                                # Update CSV with details
                                update_csv_with_details(
                                    parent_url, link, title, description, csv_filename
                                )
                                print(f"Updated details for {link}")
                            else:
                                print(f"Failed to get valid details for {link}")

                            # Add randomized delay between jobs
                            time.sleep(get_random_delay(15, 30))

                        except Exception as e:
                            print(f"Error processing in-progress job {link}: {e}")
                            continue

                    # Add longer randomized delay between parent jobs
                    time.sleep(get_random_delay(30, 60))
            browser.close()

def scrape_parent_jobs():
    """Scrape parent jobs and collect in-progress links"""
    print("Starting: Collecting parent jobs and in-progress links...")

    try:
        cookies = get_cookies()
        print("Cookies successfully loaded")
    except ValueError as e:
        print(f"Error loading cookies: {e}")
        return

    # Initialize profile manager with stability mode from env
    stability_mode = os.getenv("SESSION_STABILITY", "medium")
    profile_manager = BrowserProfileManager(stability_mode)
    print(f"Using {stability_mode} stability mode for browser profiles")

    try:
        # Collect all job links
        print("\nGetting job list...")
        try:
            job_links = scrape_parent_job_links(cookies, profile_manager)
            if not job_links:
                print("Failed to get job links")
                return
            print(f"Found jobs: {len(job_links)}")
        except Exception as e:
            print(f"Error getting job links: {e}")
            return

        # List to store all jobs
        jobs_data = []

        # Collect parent jobs and in-progress links
        print("\nCollecting parent job information and in-progress links...")
        for i, link in enumerate(job_links, 1):
            print(f"\nProcessing parent job {i}/{len(job_links)}...")
            try:
                # Get parent job details and in-progress links
                job_data = scrape_parent_job(link, cookies)
                if not job_data:
                    print(f"Failed to get parent job details for {link}")
                    continue

                jobs_data.append(job_data)

                # Add randomized delay between parent jobs
                time.sleep(get_random_delay(10, 20))

            except Exception as e:
                print(f"Error processing parent job {link}: {e}")
                continue

        # Save data to CSV
        csv_filename = save_to_csv(jobs_data)
        return csv_filename

    except Exception as e:
        print(f"Error during scraping: {e}")

if __name__ == "__main__":
    try:
        csv_filename = scrape_parent_jobs()
        if csv_filename:
            process_in_progress_jobs(csv_filename)
    except KeyboardInterrupt:
        print("\nScript execution interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

from parent_jobs import scrape_parent_job_links, scrape_parent_job
from in_progress_jobs import (
    scrape_in_progress_job,
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
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()


def get_random_delay(min_delay, max_delay, behavior="normal"):
    """Get a random delay with various distribution patterns"""
    if behavior == "quick":
        # Quick actions like mouse movements
        mu = min_delay + (max_delay - min_delay) * 0.2
        sigma = (max_delay - min_delay) / 8
    elif behavior == "reading":
        # Longer delays for content reading
        mu = min_delay + (max_delay - min_delay) * 0.7
        sigma = (max_delay - min_delay) / 4
    else:  # normal
        # Standard delays for regular actions
        mu = (min_delay + max_delay) / 2
        sigma = (max_delay - min_delay) / 6

    # Add occasional longer pauses
    if random.random() < 0.1:  # 10% chance
        mu *= 1.5
        sigma *= 1.2

    delay = random.gauss(mu, sigma)
    return max(0.1, min(max_delay, delay))


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
        "AWSALBCORS",
        "AWSALBTG",
        "AWSALBTGCORS",
    }

    # Try to load cookies from JSON file first
    try:
        json_files = [
            f for f in os.listdir() if f.endswith(".json") and "upwork.com" in f
        ]
        if json_files:
            latest_file = max(json_files, key=os.path.getctime)  # Get most recent file
            print(f"Loading cookies from {latest_file}")

            with open(latest_file, "r") as f:
                json_cookies = json.load(f)

            # Extract required cookies from JSON
            for cookie in json_cookies:
                if cookie["name"] in required_cookie_names:
                    cookies.append(
                        {
                            "name": cookie["name"],
                            "value": cookie["value"],
                            "domain": cookie.get("domain", ".upwork.com"),
                            "path": cookie.get("path", "/"),
                        }
                    )

            # Verify all required cookies are present
            found_cookies = {cookie["name"] for cookie in cookies}
            if "master_access_token" in found_cookies:
                print("Successfully loaded cookies from JSON file")
                return cookies
            else:
                print(
                    "JSON file missing critical cookies, falling back to environment variables"
                )
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
        "AWSALBCORS": "UPWORK_AWSALBCORS",
        "AWSALBTG": "UPWORK_AWSALBTG",
        "AWSALBTGCORS": "UPWORK_AWSALBTGCORS",
    }

    # Load from environment variables
    for cookie_name, env_var in env_cookie_mapping.items():
        value = os.getenv(env_var)
        if value and value != "your_master_token_here":
            cookies.append(
                {
                    "name": cookie_name,
                    "value": value,
                    "domain": ".upwork.com",
                    "path": "/",
                }
            )

    # Verify master token presence
    if not any(c["name"] == "master_access_token" for c in cookies):
        raise ValueError(
            "master_access_token not found in JSON or environment variables"
        )

    return cookies


def get_proxy():
    """Get proxy configuration with rotation support"""
    # Primary proxy
    proxy_host = os.getenv("PROXY_HOST")
    proxy_port = os.getenv("PROXY_PORT")
    proxy_username = os.getenv("PROXY_USERNAME")
    proxy_password = os.getenv("PROXY_PASSWORD")

    # Backup proxies (comma-separated lists)
    backup_hosts = os.getenv("BACKUP_PROXY_HOSTS", "").split(",")
    backup_ports = os.getenv("BACKUP_PROXY_PORTS", "").split(",")
    backup_usernames = os.getenv("BACKUP_PROXY_USERNAMES", "").split(",")
    backup_passwords = os.getenv("BACKUP_PROXY_PASSWORDS", "").split(",")

    # Add primary proxy to rotation if available
    proxies = []
    if all([proxy_host, proxy_port, proxy_username, proxy_password]):
        proxies.append({
            "server": f"http://{proxy_host.strip()}:{proxy_port.strip()}",
            "username": proxy_username.strip(),
            "password": proxy_password.strip(),
        })

    # Add backup proxies if available
    for i in range(min(len(backup_hosts), len(backup_ports), len(backup_usernames), len(backup_passwords))):
        if all([backup_hosts[i], backup_ports[i], backup_usernames[i], backup_passwords[i]]):
            proxies.append({
                "server": f"http://{backup_hosts[i].strip()}:{backup_ports[i].strip()}",
                "username": backup_usernames[i].strip(),
                "password": backup_passwords[i].strip(),
            })

    # Return random proxy from available ones
    return random.choice(proxies) if proxies else None


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

    # Session management settings
    max_jobs_per_session = int(os.getenv("MAX_JOBS_PER_SESSION", "10"))
    session_cooldown = int(os.getenv("SESSION_COOLDOWN", "300"))  # 5 minutes default
    jobs_processed = 0
    total_errors = 0
    max_consecutive_errors = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "3"))
    consecutive_errors = 0

    print("\nProcessing in-progress jobs from CSV...")
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        while rows and consecutive_errors < max_consecutive_errors:
            with sync_playwright() as p:
                proxy = get_proxy()
                print(f"\nStarting new session with proxy: {proxy['server'] if proxy else 'No proxy'}")
                
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                    proxy=proxy
                )

                session_rows = rows[:max_jobs_per_session]
                rows = rows[max_jobs_per_session:]
                
                for row in session_rows:
                    if row["in_progress_links"]:
                        parent_url = row["link"]
                        in_progress_links = row["in_progress_links"].split(" ; ")
                        print(f"\nProcessing in-progress jobs for {parent_url}")

                        for i, link in enumerate(in_progress_links, 1):
                            if not link:
                                continue
                            print(
                                f"Processing in-progress job {i}/{len(in_progress_links)}"
                            )

                            try:
                                # Get job details with retries and timeouts
                                title, description = scrape_in_progress_job(
                                    link, cookies, browser, profile_manager
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
                                    consecutive_errors = 0  # Reset error counter on success
                                    jobs_processed += 1
                                else:
                                    print(f"Failed to get valid details for {link}")
                                    consecutive_errors += 1
                                    total_errors += 1

                                # Add variable delays based on content length
                                content_length = len(description) if description else 0
                                if content_length > 1000:
                                    # Longer delay for longer content (simulating reading)
                                    time.sleep(get_random_delay(20, 40, "reading"))
                                else:
                                    # Shorter delay for brief content
                                    time.sleep(get_random_delay(10, 25, "normal"))

                            except Exception as e:
                                print(f"Error processing in-progress job {link}: {e}")
                                consecutive_errors += 1
                                total_errors += 1
                                continue

                            # Check if we need to stop due to errors
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"\nStopping due to {consecutive_errors} consecutive errors")
                                break

                        # Add variable delays between parent jobs with occasional longer pauses
                        if random.random() < 0.2:  # 20% chance for a longer break
                            time.sleep(get_random_delay(45, 90, "reading"))
                        else:
                            time.sleep(get_random_delay(25, 50, "normal"))

                browser.close()
                
                # Session cooldown if there are more jobs to process
                if rows:
                    cooldown_time = get_random_delay(session_cooldown, session_cooldown * 1.5, "reading")
                    print(f"\nSession complete. Cooling down for {int(cooldown_time)} seconds...")
                    print(f"Jobs processed: {jobs_processed}, Errors: {total_errors}")
                    time.sleep(cooldown_time)


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

    # Session management settings
    max_jobs_per_session = int(os.getenv("MAX_JOBS_PER_SESSION", "10"))
    session_cooldown = int(os.getenv("SESSION_COOLDOWN", "300"))  # 5 minutes default
    jobs_processed = 0
    total_errors = 0
    max_consecutive_errors = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "3"))
    consecutive_errors = 0

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
        remaining_links = job_links.copy()

        # Process jobs in sessions
        while remaining_links and consecutive_errors < max_consecutive_errors:
            session_links = remaining_links[:max_jobs_per_session]
            remaining_links = remaining_links[max_jobs_per_session:]

            proxy = get_proxy()
            print(f"\nStarting new session with proxy: {proxy['server'] if proxy else 'No proxy'}")

            # Collect parent jobs and in-progress links for this session
            print("\nCollecting parent job information and in-progress links...")
            for i, link in enumerate(session_links, 1):
                print(f"\nProcessing parent job {i}/{len(session_links)}...")
                try:
                    # Get parent job details and in-progress links
                    job_data = scrape_parent_job(link, cookies, profile_manager)
                    if job_data:
                        jobs_data.append(job_data)
                        consecutive_errors = 0  # Reset error counter on success
                        jobs_processed += 1
                        print(f"Successfully processed job: {job_data.get('title', 'No title')}")
                    else:
                        print(f"Failed to get parent job details for {link}")
                        consecutive_errors += 1
                        total_errors += 1

                    # Add variable delays between jobs
                    if job_data and len(job_data.get('description', '')) > 1000:
                        # Longer delay for jobs with more content
                        time.sleep(get_random_delay(15, 30, "reading"))
                    else:
                        time.sleep(get_random_delay(10, 20, "normal"))

                except Exception as e:
                    print(f"Error processing parent job {link}: {e}")
                    consecutive_errors += 1
                    total_errors += 1
                    continue

                # Check if we need to stop due to errors
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\nStopping due to {consecutive_errors} consecutive errors")
                    break

            # Session cooldown if there are more jobs to process
            if remaining_links:
                cooldown_time = get_random_delay(session_cooldown, session_cooldown * 1.5, "reading")
                print(f"\nSession complete. Cooling down for {int(cooldown_time)} seconds...")
                print(f"Jobs processed: {jobs_processed}, Errors: {total_errors}")
                time.sleep(cooldown_time)

        # Save data to CSV
        csv_filename = save_to_csv(jobs_data)
        print(f"\nFinal Statistics:")
        print(f"Total jobs processed: {jobs_processed}")
        print(f"Total errors: {total_errors}")
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

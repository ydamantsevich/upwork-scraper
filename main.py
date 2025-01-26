from parent_jobs import scrape_parent_job_links, scrape_parent_job
from in_progress_jobs import (
    find_in_progress_links,
    scrape_in_progress_job,
    update_csv_with_progress_data,
    update_csv_with_details,
)
import os
import csv
from datetime import datetime
from dotenv import load_dotenv
import time
import random
import sys

# Load environment variables from .env file
load_dotenv()


def get_cookies():
    """Get all required cookies from environment variables"""
    cookies = []

    # Main cookies for authorization
    required_cookies = {
        "master_access_token": os.getenv("UPWORK_MASTER_TOKEN"),
        "oauth2_global_js_token": os.getenv("UPWORK_OAUTH_TOKEN"),
        "visitor_id": os.getenv("UPWORK_VISITOR_ID"),
        "__cf_bm": os.getenv("UPWORK_CF_BM"),
    }

    # Check for main token presence
    if (
        not required_cookies["master_access_token"]
        or required_cookies["master_access_token"] == "your_master_token_here"
    ):
        raise ValueError("Please set your UPWORK_MASTER_TOKEN in .env file")

    # Form cookies list
    for name, value in required_cookies.items():
        if value:
            cookies.append(
                {"name": name, "value": value, "domain": ".upwork.com", "path": "/"}
            )

    return cookies


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
    """Phase 2: Process in-progress jobs from CSV and update with details"""
    try:
        cookies = get_cookies()
        print("Cookies successfully loaded")
    except ValueError as e:
        print(f"Error loading cookies: {e}")
        return

    print("\nPhase 2: Processing in-progress jobs from CSV...")
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        for row in rows:
            if row["in_progress_links"]:
                parent_url = row["url"]
                in_progress_links = row["in_progress_links"].split("|")
                print(f"\nProcessing in-progress jobs for {parent_url}")

                for i, link in enumerate(in_progress_links, 1):
                    if not link:
                        continue
                    print(f"Processing in-progress job {i}/{len(in_progress_links)}")

                    try:
                        # Get job details with retries and timeouts
                        title, description = scrape_in_progress_job(link, cookies)
                        if title and description and title != "Title not found" and description != "Description not found":
                            # Update CSV with details
                            update_csv_with_details(
                                parent_url, link, title, description, csv_filename
                            )
                            print(f"Updated details for {link}")
                        else:
                            print(f"Failed to get valid details for {link}")

                        # Add delay between jobs
                        time.sleep(random.uniform(15, 30))

                    except Exception as e:
                        print(f"Error processing in-progress job {link}: {e}")
                        continue

                # Add longer delay between parent jobs
                time.sleep(random.uniform(30, 60))


def scrape_parent_jobs():
    """Phase 1: Scrape parent jobs and collect in-progress links"""
    print("Starting Phase 1: Collecting parent jobs and in-progress links...")

    try:
        cookies = get_cookies()
        print("Cookies successfully loaded")
    except ValueError as e:
        print(f"Error loading cookies: {e}")
        return

    try:
        # Collect all job links
        print("\nGetting job list...")
        try:
            job_links = scrape_parent_job_links(cookies)
            if not job_links:
                print("Failed to get job links")
                return
            print(f"Found jobs: {len(job_links)}")
        except Exception as e:
            print(f"Error getting job links: {e}")
            return

        # List to store all jobs
        jobs_data = []

        # First phase: Collect parent jobs and in-progress links
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

                # Add delay between parent jobs
                time.sleep(random.uniform(10, 20))

            except Exception as e:
                print(f"Error processing parent job {link}: {e}")
                continue

        # Save data to CSV
        csv_filename = save_to_csv(jobs_data)
        print("\nPhase 1 complete. To process in-progress jobs, run:")
        print(f"python main.py phase2 {csv_filename}")
        return csv_filename

    except Exception as e:
        print(f"Error during scraping: {e}")


if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            # No arguments - run phase 1
            scrape_parent_jobs()
        elif len(sys.argv) == 3 and sys.argv[1] == "phase2":
            # Phase 2 with CSV filename
            csv_filename = sys.argv[2]
            if not os.path.exists(csv_filename):
                print(f"Error: CSV file {csv_filename} not found")
                sys.exit(1)
            process_in_progress_jobs(csv_filename)
        else:
            print("Usage:")
            print("Phase 1 (collect parent jobs): python main.py")
            print("Phase 2 (process in-progress): python main.py phase2 <csv_filename>")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nScript execution interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

from scrape_job_details import scrape_job_details
from scrape_job_links import scrape_job_links
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_cookies():
    """Get all required cookies from environment variables"""
    cookies = []
    
    # Main cookies for authorization
    required_cookies = {
        "master_access_token": os.getenv('UPWORK_MASTER_TOKEN'),
        "oauth2_global_js_token": os.getenv('UPWORK_OAUTH_TOKEN'),
        "visitor_id": os.getenv('UPWORK_VISITOR_ID'),
        "__cf_bm": os.getenv('UPWORK_CF_BM')
    }
    
    # Check for main token presence
    if not required_cookies["master_access_token"] or required_cookies["master_access_token"] == "your_master_token_here":
        raise ValueError("Please set your UPWORK_MASTER_TOKEN in .env file")
    
    # Form cookies list
    for name, value in required_cookies.items():
        if value:
            cookies.append({
                "name": name,
                "value": value,
                "domain": ".upwork.com",
                "path": "/"
            })
    
    return cookies

def save_to_csv(jobs_data):
    """Saves data to CSV file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upwork_jobs_{timestamp}.csv"
    
    if jobs_data:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=jobs_data[0].keys())
            writer.writeheader()
            writer.writerows(jobs_data)
        print(f"\nData saved to file: {filename}")
        print(f"Total jobs saved: {len(jobs_data)}")
    else:
        print("No data to save")

def main():
    print("Starting data collection from Upwork...")
    
    # Get cookies for authorization
    try:
        cookies = get_cookies()
        print("Cookies successfully loaded")
    except ValueError as e:
        print(f"Error loading cookies: {e}")
        return

    # Collect all job links
    print("\nGetting job list...")
    job_links = scrape_job_links(cookies)
    
    if not job_links:
        print("Failed to get job links")
        return
    
    print(f"Found jobs: {len(job_links)}")

    # List to store all jobs
    jobs_data = []

    # Go through each link and collect job data
    print("\nCollecting detailed job information...")
    for i, link in enumerate(job_links, 1):
        print(f"Processing job {i}/{len(job_links)}...")
        title, description, location = scrape_job_details(link, cookies)
        # Structure data for saving
        job_data = {
            "url": f"https://www.upwork.com{link}",
            "title": title,
            "description": description,
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "source": "upwork.com"
        }
        jobs_data.append(job_data)
    
    # Save data to CSV
    save_to_csv(jobs_data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript execution interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

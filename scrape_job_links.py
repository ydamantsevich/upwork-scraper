from playwright.sync_api import sync_playwright
import time
import random


def scrape_job_links(cookies=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Устанавливаем все необходимые cookies для авторизации
        if cookies:
            required_cookies = [
                "master_access_token",
                "oauth2_global_js_token",
                "visitor_id",
                "__cf_bm"  # CloudFlare security cookie
            ]
            
            # Проверяем наличие всех необходимых cookies
            for cookie_name in required_cookies:
                if not any(c.get("name") == cookie_name for c in cookies):
                    print(f"Warning: Missing required cookie: {cookie_name}")
                    if cookie_name == "master_access_token":
                        print("  This is the main authentication token, find it as 'master_access_token' in cookies")
                    elif cookie_name == "oauth2_global_js_token":
                        print("  This is the OAuth token, find it as 'oauth2_global_js_token' in cookies")
                    elif cookie_name == "__cf_bm":
                        print("  This is the CloudFlare protection cookie, it expires every 30 minutes")
            
            # Устанавливаем cookies
            context.add_cookies(cookies)
        
        # Небольшая пауза перед загрузкой страницы
        time.sleep(random.uniform(1.0, 2.0))
        
        page.goto(
            "https://www.upwork.com/nx/search/jobs/?amount=5000-&category2_uid=531770282580668418&hourly_rate=50-&location=Europe,Northern%20America,Israel,United%20Kingdom&per_page=10&sort=recency&t=0,1"
        )

        # Ждем загрузки страницы
        page.wait_for_selector(".air3-link")
        time.sleep(random.uniform(1.0, 2.0))

        # Собираем все ссылки на вакансии
        job_links = page.query_selector_all("a.air3-link")
        links = [link.get_attribute("href") for link in job_links]

        browser.close()
        return links


if __name__ == "__main__":
    # Пример структуры cookies для тестирования
    test_cookies = [
        {
            "name": "master_access_token",
            "value": "your_master_token",
            "domain": ".upwork.com",
            "path": "/"
        },
        {
            "name": "oauth2_global_js_token",
            "value": "your_oauth_token",
            "domain": ".upwork.com",
            "path": "/"
        },
        {
            "name": "visitor_id",
            "value": "your_visitor_id",
            "domain": ".upwork.com",
            "path": "/"
        },
        {
            "name": "__cf_bm",
            "value": "your_cf_bm_value",
            "domain": ".upwork.com",
            "path": "/"
        }
    ]
    job_links = scrape_job_links(test_cookies)
    print(job_links)

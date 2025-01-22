from playwright.sync_api import sync_playwright
import time
import random


def scrape_job_details(link, cookies=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Устанавливаем cookies если они предоставлены
        if cookies:
            context.add_cookies(cookies)

        # Небольшая пауза перед загрузкой страницы
        time.sleep(random.uniform(1.0, 2.0))

        page.goto(f"https://www.upwork.com{link}")

        # Ждем загрузки страницы
        page.wait_for_selector(".job-details-card .flex-1")
        time.sleep(random.uniform(1.0, 2.0))

        # Собираем данные
        title_element = page.query_selector(".job-details-card .flex-1")
        description_element = page.query_selector("p.text-body-sm")
        country_element = page.query_selector(
            ".cfe-ui-job-about-client li:nth-of-type(1) strong"
        )
        location_details_element = page.query_selector(
            ".cfe-ui-job-about-client li:nth-of-type(1) span:first-child"
        )

        # Проверяем наличие элементов и извлекаем текст
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

        # Формируем местоположение
        if location_details:
            location = f"{country} + {location_details}"
        else:
            location = country

        browser.close()
        return title, description, location


if __name__ == "__main__":
    job_link = "/some-job-link"  # Пример ссылки на вакансию
    title, description, location = scrape_job_details(job_link)
    print(f"Title: {title}\nDescription: {description}\nLocation: {location}")

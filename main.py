from scrape_job_details import scrape_job_details
from scrape_job_links import scrape_job_links
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

def get_cookies():
    """Получаем все необходимые cookies из переменных окружения"""
    cookies = []
    
    # Основные cookies для авторизации
    required_cookies = {
        "master_access_token": os.getenv('UPWORK_MASTER_TOKEN'),
        "oauth2_global_js_token": os.getenv('UPWORK_OAUTH_TOKEN'),
        "visitor_id": os.getenv('UPWORK_VISITOR_ID'),
        "__cf_bm": os.getenv('UPWORK_CF_BM')
    }
    
    # Проверяем наличие основного токена
    if not required_cookies["master_access_token"] or required_cookies["master_access_token"] == "your_master_token_here":
        raise ValueError("Please set your UPWORK_MASTER_TOKEN in .env file")
    
    # Формируем список cookies
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
    """Сохраняет данные в CSV файл"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upwork_jobs_{timestamp}.csv"
    
    if jobs_data:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=jobs_data[0].keys())
            writer.writeheader()
            writer.writerows(jobs_data)
        print(f"\nДанные сохранены в файл: {filename}")
        print(f"Всего сохранено вакансий: {len(jobs_data)}")
    else:
        print("Нет данных для сохранения")

def main():
    print("Начинаем сбор данных с Upwork...")
    
    # Получаем cookies для авторизации
    try:
        cookies = get_cookies()
        print("Cookies успешно загружены")
    except ValueError as e:
        print(f"Ошибка при загрузке cookies: {e}")
        return

    # Собираем все ссылки на вакансии
    print("\nПолучаем список вакансий...")
    job_links = scrape_job_links(cookies)
    
    if not job_links:
        print("Не удалось получить ссылки на вакансии")
        return
    
    print(f"Найдено вакансий: {len(job_links)}")

    # Список для хранения всех вакансий
    jobs_data = []

    # Проходим по каждой ссылке и собираем данные о вакансии
    print("\nСобираем детальную информацию о вакансиях...")
    for i, link in enumerate(job_links, 1):
        print(f"Обработка вакансии {i}/{len(job_links)}...")
        title, description, location = scrape_job_details(link, cookies)
        # Структурируем данные для сохранения
        job_data = {
            "url": f"https://www.upwork.com{link}",
            "title": title,
            "description": description,
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "source": "upwork.com"
        }
        jobs_data.append(job_data)
    
    # Сохраняем данные в CSV
    save_to_csv(jobs_data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nРабота скрипта прервана пользователем")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")

import random
from typing import Dict, List, Optional, Union
from enum import Enum


class SessionStability(Enum):
    STRICT = "strict"  # Полная смена параметров для каждого запроса
    MEDIUM = "medium"  # Смена каждые 5 заданий
    RELAXED = "relaxed"  # Смена только между родительскими заданиями


class BrowserProfileManager:
    def __init__(self, stability_mode: str = "medium"):
        self.stability_mode = SessionStability(stability_mode.lower())
        self.base_profile = self._generate_base_profile()
        self.current_profile = self.base_profile.copy()
        self.requests_count = 0
        self.parent_job_count = 0

    def _generate_base_profile(self) -> Dict[str, Union[Dict, str]]:
        """Генерирует базовый профиль браузера"""
        chrome_versions = ["119.0.0.0", "120.0.0.0", "121.0.0.0", "122.0.0.0"]
        platforms = [
            "Windows NT 10.0; Win64; x64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "X11; Linux x86_64",
            "Windows NT 10.0; WOW64",
            "Macintosh; Intel Mac OS X 10_15",
            "X11; Ubuntu; Linux x86_64",
        ]
        common_widths = [1366, 1440, 1536, 1920, 2560]
        common_heights = [768, 900, 864, 1080, 1440]
        timezones = ["America/New_York", "Europe/London", "Europe/Berlin", "Asia/Tokyo"]
        locales = ["en-US", "en-GB", "en-CA", "en-AU"]
        color_schemes = ["light", "dark"]

        return {
            "viewport": {
                "width": random.choice(common_widths),
                "height": random.choice(common_heights),
            },
            "user_agent": f"Mozilla/5.0 ({random.choice(platforms)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
            "timezone": random.choice(timezones),
            "locale": random.choice(locales),
            "color_scheme": random.choice(color_schemes),
        }

    def _should_rotate(self) -> bool:
        """Определяет, нужно ли обновить профиль"""
        if self.stability_mode == SessionStability.STRICT:
            return True
        elif self.stability_mode == SessionStability.MEDIUM:
            return self.requests_count % 5 == 0
        else:  # RELAXED
            return False

    def _rotate_partial_parameters(self) -> None:
        """Обновляет часть параметров профиля"""
        # В medium режиме меняем только user-agent и timezone
        if random.random() > 0.5:
            self.current_profile["user_agent"] = self._generate_base_profile()[
                "user_agent"
            ]
        if random.random() > 0.5:
            self.current_profile["timezone"] = self._generate_base_profile()["timezone"]

    def _rotate_full_parameters(self) -> None:
        """Полностью обновляет профиль"""
        self.current_profile = self._generate_base_profile()

    def get_profile(
        self, is_new_parent_job: bool = False
    ) -> Dict[str, Union[Dict, str]]:
        """
        Возвращает текущий профиль браузера, при необходимости обновляя его

        Args:
            is_new_parent_job: Флаг, указывающий на начало обработки нового родительского задания
        """
        if is_new_parent_job:
            self.parent_job_count += 1
            if self.stability_mode == SessionStability.RELAXED:
                self._rotate_full_parameters()
            return self.current_profile

        self.requests_count += 1

        if self._should_rotate():
            if self.stability_mode == SessionStability.STRICT:
                self._rotate_full_parameters()
            else:  # MEDIUM
                self._rotate_partial_parameters()

        return self.current_profile

    def reset_counters(self) -> None:
        """Сбрасывает счетчики запросов и родительских заданий"""
        self.requests_count = 0
        self.parent_job_count = 0

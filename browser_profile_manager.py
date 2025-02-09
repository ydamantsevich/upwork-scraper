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

    def _generate_base_profile(self) -> Dict[str, Union[Dict, str, int, float, List[str]]]:
        """Генерирует расширенный профиль браузера с реалистичными параметрами"""
        # Realistic browser versions and configurations
        chrome_versions = {
            "119.0.0.0": ["537.36", "99.0.4844.51"],
            "120.0.0.0": ["537.36", "100.0.4896.75"],
            "121.0.0.0": ["537.36", "101.0.4951.41"],
            "122.0.0.0": ["537.36", "102.0.5005.61"],
        }
        chosen_chrome = random.choice(list(chrome_versions.items()))
        chrome_version, (webkit_version, v8_version) = chosen_chrome

        # Platform-specific configurations
        platform_configs = {
            "Windows NT 10.0; Win64; x64": {
                "os": "Windows",
                "memory": [4, 8, 16, 32],
                "cores": [2, 4, 6, 8, 12],
                "screen_sizes": [(1920, 1080), (2560, 1440), (1366, 768), (1536, 864)],
                "gpu_vendors": ["NVIDIA", "AMD", "Intel"],
                "gpu_models": {
                    "NVIDIA": ["GeForce RTX 3060", "GeForce GTX 1660", "GeForce RTX 2070"],
                    "AMD": ["Radeon RX 6600", "Radeon RX 5700", "Radeon RX 580"],
                    "Intel": ["UHD Graphics 630", "Iris Xe Graphics", "HD Graphics 530"],
                },
            },
            "Macintosh; Intel Mac OS X 10_15_7": {
                "os": "MacOS",
                "memory": [8, 16, 32],
                "cores": [4, 6, 8, 10],
                "screen_sizes": [(2560, 1600), (1440, 900), (1680, 1050)],
                "gpu_vendors": ["Apple", "AMD"],
                "gpu_models": {
                    "Apple": ["M1", "M2", "M1 Pro"],
                    "AMD": ["Radeon Pro 5500M", "Radeon Pro 5600M"],
                },
            },
            "X11; Linux x86_64": {
                "os": "Linux",
                "memory": [4, 8, 16],
                "cores": [2, 4, 6, 8],
                "screen_sizes": [(1920, 1080), (1366, 768), (1440, 900)],
                "gpu_vendors": ["NVIDIA", "AMD", "Intel"],
                "gpu_models": {
                    "NVIDIA": ["GeForce GTX 1650", "GeForce GTX 1050"],
                    "AMD": ["Radeon RX 550", "Radeon RX 560"],
                    "Intel": ["HD Graphics 620", "UHD Graphics 620"],
                },
            },
        }

        # Select platform and its configuration
        platform = random.choice(list(platform_configs.keys()))
        config = platform_configs[platform]
        
        # Generate consistent screen and viewport sizes
        screen_size = random.choice(config["screen_sizes"])
        viewport_width = min(screen_size[0] - random.randint(20, 100), screen_size[0])
        viewport_height = min(screen_size[1] - random.randint(50, 150), screen_size[1])

        # Select GPU configuration
        gpu_vendor = random.choice(config["gpu_vendors"])
        gpu_model = random.choice(config["gpu_models"][gpu_vendor])

        # Generate consistent system configuration
        memory = random.choice(config["memory"])
        cores = random.choice(config["cores"])

        # Timezone and language settings based on geolocation
        timezone_locale_pairs = {
            "America/New_York": ["en-US"],
            "Europe/London": ["en-GB"],
            "Europe/Berlin": ["de-DE", "en-DE"],
            "Europe/Paris": ["fr-FR", "en-FR"],
            "Asia/Tokyo": ["ja-JP", "en-JP"],
            "Australia/Sydney": ["en-AU"],
            "Europe/Moscow": ["ru-RU", "en-RU"],
            "Asia/Shanghai": ["zh-CN", "en-CN"],
        }
        timezone = random.choice(list(timezone_locale_pairs.keys()))
        locale = random.choice(timezone_locale_pairs[timezone])

        # Build the complete profile
        return {
            "viewport": {
                "width": viewport_width,
                "height": viewport_height,
            },
            "screen": {
                "width": screen_size[0],
                "height": screen_size[1],
                "depth": random.choice([24, 32]),
            },
            "user_agent": f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}",
            "navigator": {
                "hardware_concurrency": cores,
                "device_memory": memory,
                "platform": config["os"].lower(),
                "vendor": "Google Inc.",
                "max_touch_points": 0 if random.random() > 0.2 else random.choice([1, 2, 5, 10]),
            },
            "webgl": {
                "vendor": gpu_vendor,
                "renderer": f"{gpu_vendor} {gpu_model}",
                "version": chrome_version,
            },
            "media_devices": {
                "audio_inputs": random.randint(1, 3),
                "audio_outputs": random.randint(1, 4),
                "video_inputs": random.randint(0, 2),
            },
            "timezone": timezone,
            "locale": locale,
            "color_scheme": random.choice(["light", "dark"]),
            "preferred_languages": [locale, "en"] if locale != "en-US" else ["en-US"],
            "do_not_track": random.choice([0, 1]),
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

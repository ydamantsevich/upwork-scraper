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

            # Add advanced browser fingerprint evasion
            page.evaluate(
                """(profile) => {
                    // Advanced WebDriver evasion
                    delete Object.getPrototypeOf(navigator).webdriver;
                    
                    // Hardware concurrency and device memory
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => profile.navigator.hardware_concurrency
                    });
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => profile.navigator.device_memory
                    });
                    
                    // Platform and vendor
                    Object.defineProperty(navigator, 'platform', {
                        get: () => profile.navigator.platform
                    });
                    Object.defineProperty(navigator, 'vendor', {
                        get: () => profile.navigator.vendor
                    });
                    
                    // Languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => profile.preferred_languages
                    });
                    
                    // Screen properties
                    Object.defineProperties(screen, {
                        width: { get: () => profile.screen.width },
                        height: { get: () => profile.screen.height },
                        colorDepth: { get: () => profile.screen.depth },
                        pixelDepth: { get: () => profile.screen.depth }
                    });
                    
                    // Advanced WebGL fingerprint
                    const getParameterProxyHandler = {
                        apply: function(target, thisArg, args) {
                            const param = args[0];
                            const gl = thisArg;
                            
                            // UNMASKED_VENDOR_WEBGL
                            if (param === 37445) {
                                return profile.webgl.vendor;
                            }
                            
                            // UNMASKED_RENDERER_WEBGL
                            if (param === 37446) {
                                return profile.webgl.renderer;
                            }
                            
                            return target.apply(thisArg, args);
                        }
                    };
                    
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = new Proxy(getParameter, getParameterProxyHandler);
                    
                    // Advanced Chrome runtime
                    window.chrome = {
                        app: {
                            isInstalled: false,
                            getDetails: function() { return null; },
                            getIsInstalled: function() { return false; },
                            runningState: function() { return 'cannot_run'; }
                        },
                        runtime: {
                            OnInstalledReason: {},
                            OnRestartRequiredReason: {},
                            PlatformArch: {},
                            PlatformNaclArch: {},
                            PlatformOs: {},
                            RequestUpdateCheckStatus: {},
                            connect: function() {},
                            id: undefined,
                            reload: function() {}
                        }
                    };
                    
                    // Media devices initialization and mocking
                    navigator.mediaDevices = navigator.mediaDevices || {};
                    const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                    navigator.mediaDevices.enumerateDevices = originalEnumerateDevices || (async function() {
                        const realDevices = originalEnumerateDevices ? await originalEnumerateDevices.apply(this) : [];
                        const audioInputs = profile.media_devices.audio_inputs;
                        const audioOutputs = profile.media_devices.audio_outputs;
                        const videoInputs = profile.media_devices.video_inputs;
                        
                        return Array(audioInputs + audioOutputs + videoInputs).fill().map((_, i) => ({
                            deviceId: `device-${i}-${Math.random().toString(36).substr(2, 9)}`,
                            groupId: `group-${Math.floor(i/2)}-${Math.random().toString(36).substr(2, 9)}`,
                            kind: i < audioInputs ? 'audioinput' : i < (audioInputs + audioOutputs) ? 'audiooutput' : 'videoinput',
                            label: ''
                        }));
                    })();
                    
                    // Permissions API
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = async function(params) {
                        if (params.name === 'notifications') {
                            return { state: Notification.permission };
                        }
                        return originalQuery.call(this, params);
                    };
                    
                    // Do Not Track
                    Object.defineProperty(navigator, 'doNotTrack', {
                        get: () => profile.do_not_track
                    });
                    
                }""",
                profile_manager.current_profile
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

            # Add advanced browser fingerprint evasion
            page.evaluate(
                """(profile) => {
                    // Advanced WebDriver evasion
                    delete Object.getPrototypeOf(navigator).webdriver;
                    
                    // Hardware concurrency and device memory
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => profile.navigator.hardware_concurrency
                    });
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => profile.navigator.device_memory
                    });
                    
                    // Platform and vendor
                    Object.defineProperty(navigator, 'platform', {
                        get: () => profile.navigator.platform
                    });
                    Object.defineProperty(navigator, 'vendor', {
                        get: () => profile.navigator.vendor
                    });
                    
                    // Languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => profile.preferred_languages
                    });
                    
                    // Screen properties
                    Object.defineProperties(screen, {
                        width: { get: () => profile.screen.width },
                        height: { get: () => profile.screen.height },
                        colorDepth: { get: () => profile.screen.depth },
                        pixelDepth: { get: () => profile.screen.depth }
                    });
                    
                    // Advanced WebGL fingerprint
                    const getParameterProxyHandler = {
                        apply: function(target, thisArg, args) {
                            const param = args[0];
                            const gl = thisArg;
                            
                            // UNMASKED_VENDOR_WEBGL
                            if (param === 37445) {
                                return profile.webgl.vendor;
                            }
                            
                            // UNMASKED_RENDERER_WEBGL
                            if (param === 37446) {
                                return profile.webgl.renderer;
                            }
                            
                            return target.apply(thisArg, args);
                        }
                    };
                    
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = new Proxy(getParameter, getParameterProxyHandler);
                    
                    // Advanced Chrome runtime
                    window.chrome = {
                        app: {
                            isInstalled: false,
                            getDetails: function() { return null; },
                            getIsInstalled: function() { return false; },
                            runningState: function() { return 'cannot_run'; }
                        },
                        runtime: {
                            OnInstalledReason: {},
                            OnRestartRequiredReason: {},
                            PlatformArch: {},
                            PlatformNaclArch: {},
                            PlatformOs: {},
                            RequestUpdateCheckStatus: {},
                            connect: function() {},
                            id: undefined,
                            reload: function() {}
                        }
                    };
                    
                    // Media devices initialization and mocking
                    navigator.mediaDevices = navigator.mediaDevices || {};
                    const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                    navigator.mediaDevices.enumerateDevices = originalEnumerateDevices || (async function() {
                        const realDevices = originalEnumerateDevices ? await originalEnumerateDevices.apply(this) : [];
                        const audioInputs = profile.media_devices.audio_inputs;
                        const audioOutputs = profile.media_devices.audio_outputs;
                        const videoInputs = profile.media_devices.video_inputs;
                        
                        return Array(audioInputs + audioOutputs + videoInputs).fill().map((_, i) => ({
                            deviceId: `device-${i}-${Math.random().toString(36).substr(2, 9)}`,
                            groupId: `group-${Math.floor(i/2)}-${Math.random().toString(36).substr(2, 9)}`,
                            kind: i < audioInputs ? 'audioinput' : i < (audioInputs + audioOutputs) ? 'audiooutput' : 'videoinput',
                            label: ''
                        }));
                    });
                    
                    // Permissions API
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = async function(params) {
                        if (params.name === 'notifications') {
                            return { state: Notification.permission };
                        }
                        return originalQuery.call(this, params);
                    };
                    
                    // Do Not Track
                    Object.defineProperty(navigator, 'doNotTrack', {
                        get: () => profile.do_not_track
                    });
                    
                }""",
                profile_manager.current_profile
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
                        "link": f"https://www.upwork.com{link}",
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

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time
import random
import csv


def get_random_user_agent():
    """Generate a random modern user agent"""
    chrome_versions = ["119.0.0.0", "120.0.0.0", "121.0.0.0", "122.0.0.0"]
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64",
        "Windows NT 10.0; WOW64",
        "Macintosh; Intel Mac OS X 10_15",
        "X11; Ubuntu; Linux x86_64",
    ]
    return f"Mozilla/5.0 ({random.choice(platforms)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36"


def get_random_viewport():
    """Generate random viewport sizes that look natural"""
    common_widths = [1366, 1440, 1536, 1920, 2560]
    common_heights = [768, 900, 864, 1080, 1440]
    return {
        "width": random.choice(common_widths),
        "height": random.choice(common_heights),
    }


def generate_bezier_curve(start, end, num_points=10):
    """Generate a natural bezier curve for mouse movement"""
    control_point1 = (
        start[0] + (end[0] - start[0]) * random.uniform(0.2, 0.4),
        start[1] + random.uniform(-100, 100),
    )
    control_point2 = (
        start[0] + (end[0] - start[0]) * random.uniform(0.6, 0.8),
        end[1] + random.uniform(-100, 100),
    )

    points = []
    for t in [i / (num_points - 1) for i in range(num_points)]:
        # Bezier curve formula
        x = (
            (1 - t) ** 3 * start[0]
            + 3 * (1 - t) ** 2 * t * control_point1[0]
            + 3 * (1 - t) * t**2 * control_point2[0]
            + t**3 * end[0]
        )
        y = (
            (1 - t) ** 3 * start[1]
            + 3 * (1 - t) ** 2 * t * control_point1[1]
            + 3 * (1 - t) * t**2 * control_point2[1]
            + t**3 * end[1]
        )
        points.append((int(x), int(y)))
    return points


def natural_scroll_pattern():
    """Generate natural scrolling patterns"""
    patterns = [
        # Quick scroll followed by reading pauses
        lambda: ([random.randint(300, 500)] + [50] * random.randint(2, 4)),
        # Gradual scroll while reading
        lambda: [random.randint(50, 150) for _ in range(random.randint(3, 7))],
        # Long scroll followed by scroll up correction
        lambda: [random.randint(400, 800), random.randint(-100, -50)],
        # Variable speed scrolling
        lambda: [random.randint(100, 300) for _ in range(random.randint(2, 5))],
    ]
    return random.choice(patterns)()


def simulate_human_behavior(page):
    """Simulate highly realistic human behavior with natural patterns"""
    viewport_width = page.viewport_size["width"]
    viewport_height = page.viewport_size["height"]
    current_mouse_pos = {"x": 0, "y": 0}  # Track mouse position

    # Initial page load pause with slight variation
    time.sleep(random.normalvariate(2.5, 0.5))

    # Simulate initial page scan
    start_pos = (random.randint(0, viewport_width), random.randint(50, 150))
    page.mouse.move(start_pos[0], start_pos[1])
    current_mouse_pos["x"], current_mouse_pos["y"] = start_pos
    time.sleep(random.normalvariate(0.5, 0.1))

    # Natural mouse movements using bezier curves
    for _ in range(random.randint(2, 5)):
        end_pos = (
            random.randint(100, viewport_width - 100),
            random.randint(100, viewport_height - 100),
        )
        points = generate_bezier_curve(
            (current_mouse_pos["x"], current_mouse_pos["y"]),
            end_pos,
            num_points=random.randint(8, 15),
        )

        for point in points:
            page.mouse.move(point[0], point[1])
            current_mouse_pos["x"], current_mouse_pos["y"] = point
            # Add micro-delays for more natural movement
            time.sleep(random.normalvariate(0.05, 0.01))

        # Occasional mouse acceleration/deceleration
        if random.random() < 0.3:
            time.sleep(random.normalvariate(0.2, 0.05))

        # Simulate reading pause
        if random.random() < 0.4:
            time.sleep(random.normalvariate(1.0, 0.2))

    # Natural scrolling behavior
    scroll_count = random.randint(2, 5)
    for _ in range(scroll_count):
        # Get scroll pattern
        scroll_amounts = natural_scroll_pattern()

        for amount in scroll_amounts:
            # Add slight mouse movement during scroll
            if random.random() < 0.3:
                new_x = current_mouse_pos["x"] + random.randint(-20, 20)
                new_y = current_mouse_pos["y"] + random.randint(-20, 20)
                # Keep mouse within viewport
                new_x = max(0, min(new_x, viewport_width))
                new_y = max(0, min(new_y, viewport_height))
                page.mouse.move(new_x, new_y)
                current_mouse_pos["x"], current_mouse_pos["y"] = new_x, new_y

            page.mouse.wheel(0, amount)
            # Variable scroll speed
            time.sleep(random.normalvariate(0.3, 0.1))

            # Simulate content scanning pause
            if random.random() < 0.3:
                time.sleep(random.normalvariate(0.8, 0.2))

    # Occasional highlight/select text behavior
    if random.random() < 0.2:
        start_x = current_mouse_pos["x"]
        start_y = current_mouse_pos["y"]
        page.mouse.down()
        new_x = start_x + random.randint(50, 200)
        new_y = start_y + random.randint(-10, 10)
        # Keep within viewport
        new_x = max(0, min(new_x, viewport_width))
        new_y = max(0, min(new_y, viewport_height))
        page.mouse.move(new_x, new_y)
        current_mouse_pos["x"], current_mouse_pos["y"] = new_x, new_y
        time.sleep(random.normalvariate(0.3, 0.05))
        page.mouse.up()
        time.sleep(random.normalvariate(0.5, 0.1))


def find_in_progress_links(page, max_retries=3):
    """Find in-progress job links with retries"""
    in_progress_links = []

    for attempt in range(max_retries):
        try:
            print("Looking for in-progress button...")
            simulate_human_behavior(page)

            in_progress_button = page.query_selector(".jobs-in-progress-title")

            if not in_progress_button:
                print("No in-progress button found")
                return []

            print("Found in-progress button, clicking...")
            # Move mouse naturally to button before clicking
            button_box = in_progress_button.bounding_box()
            if button_box:
                page.mouse.move(
                    button_box["x"] + button_box["width"] / 2 + random.uniform(-5, 5),
                    button_box["y"] + button_box["height"] / 2 + random.uniform(-5, 5),
                    steps=random.randint(5, 10),
                )
                time.sleep(random.uniform(0.3, 0.7))

            in_progress_button.click()
            time.sleep(random.uniform(2.0, 3.0))

            # Wait for the in-progress section to load
            page.wait_for_selector(
                ".air3-card-section:first-child .js-job-link", timeout=30000
            )

            simulate_human_behavior(page)

            # Get all in-progress job elements
            print("Looking for in-progress jobs...")
            in_progress_jobs = page.query_selector_all(
                ".air3-card-section:first-child .js-job-link"
            )
            print(f"Found {len(in_progress_jobs)} in-progress jobs")

            for job in in_progress_jobs:
                url = job.get_attribute("href")
                if url and url not in in_progress_links:
                    in_progress_links.append(f"https://www.upwork.com{url}")
                    print(f"Found in-progress link: {url}")
                    time.sleep(
                        random.uniform(2.0, 3.0)
                    )  # Add delay between collecting links

            if in_progress_links:
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(5.0, 8.0))
                try:
                    in_progress_button = page.query_selector(".jobs-in-progress-title")
                    if in_progress_button:
                        in_progress_button.click()
                except:
                    pass
            else:
                print("Max retries reached for finding in-progress links")

    return in_progress_links


def scrape_in_progress_job(
    url, cookies, browser=None, profile_manager=None, max_retries=3
):
    """Scrape details for a single in-progress job with retries, reusing browser instance"""
    if not browser:
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
        profile = profile_manager.get_profile()
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
            profile_manager.current_profile,
        )

        for attempt in range(max_retries):
            try:
                simulate_human_behavior(page)

                response = page.goto(
                    f"{url}",
                    wait_until="networkidle",
                    timeout=60000,
                )

                if response.status != 200:
                    print(f"Warning: Page returned status code {response.status}")
                    page.screenshot(path=f"error_screenshot_{attempt}.png")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(15.0, 25.0))
                    continue

                if page.query_selector("div[class*='captcha']") or page.query_selector(
                    "div[class*='security-check']"
                ):
                    print("Warning: Detected possible CAPTCHA or security check page")
                    page.screenshot(path=f"captcha_progress_screenshot_{attempt}.png")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(20.0, 30.0))
                        continue
                    raise Exception("Security check or CAPTCHA detected")

                simulate_human_behavior(page)

                title_element = page.wait_for_selector(
                    ".job-details-card .flex-1", timeout=45000, state="visible"
                )

                description_element = page.wait_for_selector(
                    "p.text-body-sm", timeout=30000
                )

                title = (
                    title_element.inner_text() if title_element else "Title not found"
                )
                description = (
                    description_element.inner_text()
                    if description_element
                    else "Description not found"
                )

                if (
                    title != "Title not found"
                    and description != "Description not found"
                ):
                    return title, description

                print(
                    f"Attempt {attempt + 1}: Title or description not found, retrying..."
                )
                time.sleep(random.uniform(8.0, 12.0))

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(15.0, 25.0))
                else:
                    raise

        return "Title not found", "Description not found"

    finally:
        page.close()
        if not browser:
            browser.close()


def update_csv_with_progress_data(parent_url, in_progress_links, csv_filename):
    """Updates the CSV file with in_progress_links for the parent job"""
    rows = []
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["link"] == parent_url:
                row["in_progress_links"] = (
                    " ; ".join(in_progress_links) if in_progress_links else ""
                )
            rows.append(row)

    with open(csv_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def update_csv_with_details(
    parent_url, in_progress_url, title, description, csv_filename
):
    """Updates the CSV with title and description for an in-progress job"""
    rows = []
    with open(csv_filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["link"] == parent_url:
                titles = (
                    row["in_progress_titles"].split(" ; ")
                    if row["in_progress_titles"]
                    else []
                )
                descriptions = (
                    row["in_progress_descriptions"].split(" ; ")
                    if row["in_progress_descriptions"]
                    else []
                )
                links = (
                    row["in_progress_links"].split(" ; ")
                    if row["in_progress_links"]
                    else []
                )

                try:
                    clean_links = [
                        link.replace("https://www.upwork.com", "") for link in links
                    ]
                    in_progress_url_cleaned = in_progress_url.replace("https://www.upwork.com", "")
                    idx = clean_links.index(in_progress_url_cleaned)
                    while len(titles) <= idx:
                        titles.append("")
                    while len(descriptions) <= idx:
                        descriptions.append("")

                    titles[idx] = title
                    descriptions[idx] = description

                    row["in_progress_titles"] = " ; ".join(titles)
                    row["in_progress_descriptions"] = " ; ".join(descriptions)
                except ValueError:
                    print(
                        f"Link {in_progress_url} not found in parent job {parent_url}"
                    )
            rows.append(row)

    with open(csv_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

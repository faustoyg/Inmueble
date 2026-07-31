
#Plusvalia.com Property Listing Scraper (Selenium)
#==================================================


import re
import time
import uuid
import random
import logging
from dataclasses import dataclass, asdict, field
from typing import Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# CONFIG -- valores ajustables
# --------------------------------------------------------------------------
CITY_SLUG = "quito"          # used to build the search URL, e.g. "quito", "guayaquil", "manta"
CITY_LABEL = "Quito"         # value written to the CITY column in the output CSV
PROPERTY_TYPE = "casas"      # "casas" or "departamentos"
OPERATION = "venta"          # "venta" (sale) or "alquiler" (rent)
MAX_PAGES = 5                # how many result pages to crawl (each page ~20-30 listings)
HEADLESS = True              # set False to watch the browser while debugging
FETCH_COORDINATES = False    # OPTIONAL second stage -- see warning above
REQUEST_DELAY_RANGE = (2, 4) # seconds, randomized delay between page loads
OUTPUT_CSV = "plusvalia_scraped.csv"  # saved in the same folder you run the script from


def build_listing_url(page: int) -> str:
    """
    Builds the search results URL for a given page number.
    Page 1: https://www.plusvalia.com/{PROPERTY_TYPE}-en-{OPERATION}-en-{CITY_SLUG}.html
    Page N: https://www.plusvalia.com/{PROPERTY_TYPE}-en-{OPERATION}-en-{CITY_SLUG}-pagina-{N}.html
    """
    base = f"https://www.plusvalia.com/{PROPERTY_TYPE}-en-{OPERATION}-en-{CITY_SLUG}"
    if page == 1:
        return f"{base}.html"
    return f"{base}-pagina-{page}.html"


@dataclass
class Listing:
    ID: str = field(default_factory=lambda: str(uuid.uuid4()))
    CITY: str = ""
    PRICE_USD: Optional[int] = None
    BEDROOMS: Optional[int] = None
    BATHROOMS: Optional[int] = None
    PARKING_SPOTS: Optional[int] = None
    CONSTRUCTION_AREA_SQM: Optional[float] = None
    LATITUDE: Optional[float] = None
    LONGITUDE: Optional[float] = None
    LINK: str = ""


def make_driver() -> webdriver.Chrome:
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1000")
    # A realistic UA reduces (but doesn't eliminate) the chance of being blocked
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    # Selenium 4.6+ auto-detects/downloads the right ChromeDriver via
    # Selenium Manager -- no Service(...) or driver path needed.
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def parse_number(text: str) -> Optional[float]:
    """Extracts the first numeric value from a string like '3 hab.' -> 3"""
    match = re.search(r"[\d.,]+", text)
    if not match:
        return None
    cleaned = match.group().replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_card(card_text: str, link: str) -> Listing:

    listing = Listing(CITY=CITY_LABEL, LINK=link)

    price_match = re.search(r"USD\s*([\d.,]+)", card_text)
    if price_match:
        listing.PRICE_USD = int(parse_number(price_match.group(1)) or 0)

    area_match = re.search(r"([\d.,]+)\s*m²\s*tot", card_text)
    if area_match:
        listing.CONSTRUCTION_AREA_SQM = parse_number(area_match.group(1))

    bed_match = re.search(r"(\d+)\s*hab", card_text)
    if bed_match:
        listing.BEDROOMS = int(bed_match.group(1))

    bath_match = re.search(r"(\d+)\s*ba[ñn]o", card_text)
    if bath_match:
        listing.BATHROOMS = int(bath_match.group(1))

    park_match = re.search(r"(\d+)\s*estac", card_text)
    if park_match:
        listing.PARKING_SPOTS = int(park_match.group(1))

    return listing


def scrape_listing_page(driver: webdriver.Chrome, url: str) -> list[Listing]:
    log.info(f"Loading: {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/propiedades/']"))
        )
    except TimeoutException:
        log.warning(f"No listings found (or blocked) on {url}")
        return []

    anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/propiedades/']")

    results = []
    seen_links = set()
    for a in anchors:
        try:
            href = a.get_attribute("href")
            if not href or href in seen_links:
                continue
            seen_links.add(href)

            # Walk up a few levels to find a container with the card's full text
            container = a
            card_text = ""
            for _ in range(5):
                try:
                    container = container.find_element(By.XPATH, "..")
                    text = container.text
                    if "USD" in text and ("hab" in text or "m²" in text):
                        card_text = text
                        break
                except NoSuchElementException:
                    break

            if not card_text:
                continue

            listing = parse_card(card_text, href)
            results.append(listing)
        except Exception as e:
            log.debug(f"Skipping a card due to error: {e}")
            continue

    log.info(f"Parsed {len(results)} listings from this page")
    return results


def fetch_coordinates(driver: webdriver.Chrome, listing: Listing) -> None:

    try:
        driver.get(listing.LINK)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source

        # Try a few common patterns seen on Navent-family sites
        patterns = [
            r'"lat"\s*:\s*(-?\d+\.\d+)\s*,\s*"lon"\s*:\s*(-?\d+\.\d+)',
            r'"latitude"\s*:\s*(-?\d+\.\d+)\s*,\s*"longitude"\s*:\s*(-?\d+\.\d+)',
            r'lat=(-?\d+\.\d+)&(?:amp;)?lng=(-?\d+\.\d+)',
            r'center=(-?\d+\.\d+)%2C(-?\d+\.\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, page_source)
            if match:
                listing.LATITUDE = float(match.group(1))
                listing.LONGITUDE = float(match.group(2))
                break

        if listing.LATITUDE is None:
            log.warning(f"Could not find coordinates for {listing.LINK}")

    except Exception as e:
        log.warning(f"Failed to fetch coordinates for {listing.LINK}: {e}")


def main():
    driver = make_driver()
    all_listings: list[Listing] = []

    try:
        for page in range(1, MAX_PAGES + 1):
            url = build_listing_url(page)
            page_listings = scrape_listing_page(driver, url)
            if not page_listings:
                log.info("No more listings found -- stopping pagination early.")
                break
            all_listings.extend(page_listings)
            time.sleep(random.uniform(*REQUEST_DELAY_RANGE))

        if FETCH_COORDINATES:
            log.info("Fetching coordinates for each property (this will be slow)...")
            for listing in all_listings:
                fetch_coordinates(driver, listing)
                time.sleep(random.uniform(*REQUEST_DELAY_RANGE))

    finally:
        driver.quit()

    df = pd.DataFrame([asdict(l) for l in all_listings])
    # Match the column order of the reference CSV
    column_order = [
        "ID", "CITY", "PRICE_USD", "BEDROOMS", "BATHROOMS",
        "PARKING_SPOTS", "CONSTRUCTION_AREA_SQM", "LATITUDE", "LONGITUDE", "LINK",
    ]
    df = df[column_order]
    df.to_csv(OUTPUT_CSV, index=False)
    log.info(f"Saved {len(df)} listings to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
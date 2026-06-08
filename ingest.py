"""
ingest.py — Document Ingestion for Berkeley Food Guide RAG
Scrapes all 10 sources from planning.md and saves raw text to documents/

Sources:
  1.  Berkeley Dining Menus  (dining.berkeley.edu)
  2.  DailyCal — Campus eateries guide
  3.  DailyCal — Coffee & study spots
  4.  DailyCal — Plant-based & sustainable eats
  5.  Travelling Foodie blog
  6.  DailyCal — 2025 Best of Berkeley food edition
  7.  Michelin Guide Berkeley
  8.  SF Eater — Best restaurants Berkeley
  9.  GrubHub Berkeley
  10. DailyCal — Best breakfast spots

Usage:
    pip install requests beautifulsoup4
    python ingest.py

Output: one .txt file per source saved in documents/
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = "documents"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def save(filename: str, text: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.strip())
    print(f"  ✓  Saved {path}  ({len(text):,} chars)")


def fetch_html(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  ✗  Could not fetch {url}: {e}")
        return None


def get_text_from_tags(soup: BeautifulSoup, tags: list[str]) -> str:
    parts = []
    for tag in tags:
        for el in soup.find_all(tag):
            t = el.get_text(separator=" ", strip=True)
            if t:
                parts.append(t)
    return "\n".join(parts)


def ingest_generic_blog(url: str, filename: str, label: str) -> None:
    """Generic scraper for article/blog pages (DailyCal, Travelling Foodie, etc.)"""
    print(f"\n{label}...")
    soup = fetch_html(url)
    if not soup:
        return
    for el in soup.find_all(["nav", "footer", "script", "style", "aside", "header"]):
        el.decompose()
    text = get_text_from_tags(soup, ["h1", "h2", "h3", "p", "li"])
    save(filename, text)


# ── Source-specific scrapers ──────────────────────────────────────────────────

def ingest_berkeley_dining():
    """Source 1 — Berkeley Dining Menus"""
    print("\n[1/10] Berkeley Dining Menus...")
    url = "https://dining.berkeley.edu/menus/"
    soup = fetch_html(url)
    if not soup:
        return
    for el in soup.find_all(["nav", "footer", "script", "style"]):
        el.decompose()
    text = soup.get_text(separator="\n", strip=True)
    save("berkeley_dining_menus.txt", text)


def ingest_michelin():
    """Source 7 — Michelin Guide Berkeley"""
    print("\n[7/10] Michelin Guide...")
    url = "https://guide.michelin.com/us/en/california/berkeley/restaurants"
    soup = fetch_html(url)
    if not soup:
        return
    for el in soup.find_all(["nav", "footer", "script", "style"]):
        el.decompose()
    text = get_text_from_tags(soup, ["h1", "h2", "h3", "p", "span", "li"])
    save("michelin_berkeley.txt", text)


def ingest_sf_eater():
    """Source 8 — SF Eater best restaurants Berkeley"""
    print("\n[8/10] SF Eater...")
    url = "https://sf.eater.com/maps/best-restaurants-berkeley"
    soup = fetch_html(url)
    if not soup:
        return
    for el in soup.find_all(["nav", "footer", "script", "style", "aside"]):
        el.decompose()
    text = get_text_from_tags(soup, ["h1", "h2", "h3", "p", "li"])
    save("sf_eater_best_berkeley.txt", text)


def ingest_grubhub():
    """Source 9 — GrubHub Berkeley (JS-heavy; extracts JSON-LD where available)"""
    print("\n[9/10] GrubHub Berkeley...")
    url = (
        "https://www.grubhub.com/search?orderMethod=delivery&locationMode=DELIVERY"
        "&facetSet=umamiV6&pageSize=36&hideHateos=true&searchMetrics=true"
        "&latitude=37.87152099&longitude=-122.27304078&geohash=9q9p3w73xehw"
        "&sortSetId=umamiV3&countOmittingTimes=true&tab=all"
        "&includeOffers=true&featureControl=fastTagBadges%3Atrue"
    )
    soup = fetch_html(url)
    if not soup:
        return
    parts = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            obj = json.loads(script.string or "")
            items = obj if isinstance(obj, list) else [obj]
            for item in items:
                if item.get("name"):
                    parts.append(f"RESTAURANT: {item['name']}")
                if item.get("description"):
                    parts.append(item["description"])
        except Exception:
            pass
    if not parts:
        # Fallback: grab whatever visible text rendered
        parts.append(soup.get_text(separator="\n", strip=True))
    save("grubhub_berkeley.txt", "\n".join(parts))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Berkeley Food Guide — Document Ingestion")
    print("=" * 60)

    # 1 — Berkeley Dining
    ingest_berkeley_dining()
    time.sleep(1)

    # 2 — DailyCal campus eateries
    ingest_generic_blog(
        url="https://www.dailycal.org/a-uc-berkeley-foodie-s-guide-to-campus-eateries/article_9823ab86-61ca-42d8-9418-06f11251be3b.html",
        filename="dailycal_campus_eateries.txt",
        label="[2/10] DailyCal — Campus eateries",
    )
    time.sleep(1)

    # 3 — DailyCal coffee & study spots
    ingest_generic_blog(
        url="https://www.dailycal.org/blogs/food-blog/tour-around-berkeley-s-best-coffee-and-study-spots/article_6c1f73a1-d93c-4f7f-a52c-1889db00589f.html",
        filename="dailycal_coffee_study_spots.txt",
        label="[3/10] DailyCal — Coffee & study spots",
    )
    time.sleep(1)

    # 4 — DailyCal plant-based & sustainable
    ingest_generic_blog(
        url="https://www.dailycal.org/blogs/a-taste-of-berkeley-s-plant-based-and-sustainable-eats/article_e76f9d3c-bdcd-456d-99bd-f7b17ab65b6d.html",
        filename="dailycal_plant_based.txt",
        label="[4/10] DailyCal — Plant-based & sustainable",
    )
    time.sleep(1)

    # 5 — Travelling Foodie
    ingest_generic_blog(
        url="https://travellingfoodie.net/places-to-eat-in-berkeley/",
        filename="travelling_foodie_berkeley.txt",
        label="[5/10] Travelling Foodie",
    )
    time.sleep(1)

    # 6 — DailyCal 2025 best of Berkeley
    ingest_generic_blog(
        url="https://www.dailycal.org/2025-best-of-berkeley-food-edition/article_39fd173d-688c-4262-b429-d2051c998c98.html",
        filename="dailycal_best_of_2025.txt",
        label="[6/10] DailyCal — 2025 Best of Berkeley",
    )
    time.sleep(1)

    # 7 — Michelin
    ingest_michelin()
    time.sleep(1)

    # 8 — SF Eater
    ingest_sf_eater()
    time.sleep(1)

    # 9 — GrubHub
    ingest_grubhub()
    time.sleep(1)

    # 10 — DailyCal breakfast spots
    ingest_generic_blog(
        url="https://www.dailycal.org/blogs/food-blog/best-breakfast-spots-in-berkeley/article_0ba9913b-da5a-4fd8-9966-f0719abc9e1e.html",
        filename="dailycal_breakfast.txt",
        label="[10/10] DailyCal — Best breakfast spots",
    )

    print("\n" + "=" * 60)
    print("  Ingestion complete! Check the documents/ folder.")
    print("=" * 60)


if __name__ == "__main__":
    main()
# app.py
# RightFit backend using DuckDuckGo image search for live product images
# Requirements: Flask, requests
# Add to requirements.txt: Flask==2.2.5, requests==2.31.0

import os
import re
import time
import logging
from urllib.parse import quote_plus

import requests
from flask import Flask, render_template, request, jsonify

# Basic logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rightfit")

app = Flask(__name__, static_folder='static', template_folder='templates')

# ----------------------
# Sizing / mapping utils
# ----------------------
def cup_group_from_diff(diff: int) -> str:
    """Map cup difference to a coarse cup-group for image selection."""
    if diff < 14:
        return "small"   # A/B
    if 14 <= diff < 16:
        return "medium"  # C/D
    return "large"       # DD/E+

def activity_key_name(activity_label: str) -> str:
    """Map frontend activity label to filename key."""
    mapping = {
        'Daily / Casual': 'casual',
        'Daily/Casual': 'casual',
        'Daily': 'casual',
        'Casual': 'casual',
        'Sports / Active': 'sports',
        'Sports/Active': 'sports',
        'Sports': 'sports',
        'High Impact': 'highimpact',
        'High-Impact': 'highimpact',
        'HighImpact': 'highimpact'
    }
    return mapping.get(activity_label, 'casual')

# ----------------------
# DuckDuckGo image search
# ----------------------
DDG_BASE = "https://duckduckgo.com/"
DDG_IJS = "https://duckduckgo.com/i.js"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://duckduckgo.com/"
}

VQD_RE = re.compile(r"vqd='(?P<vqd>[\d-]+.*?)'")  # pattern to extract vqd token


def get_vqd_token(query: str, max_tries: int = 2) -> str | None:
    """
    Obtain the 'vqd' token DuckDuckGo uses for its image JSON endpoint.
    Returns token string or None on failure.
    """
    params = {"q": query}
    for attempt in range(1, max_tries + 1):
        try:
            r = requests.get(DDG_BASE, params=params, headers=HEADERS, timeout=8)
            text = r.text
            m = VQD_RE.search(text)
            if m:
                token = m.group("vqd")
                log.debug("Obtained vqd token for query '%s': %s", query, token)
                return token
        except Exception as e:
            log.warning("vqd request attempt %s failed: %s", attempt, e)
        time.sleep(0.5 * attempt)
    log.warning("Failed to obtain vqd token for query: %s", query)
    return None


def duckduckgo_image_search(query: str, max_results: int = 8) -> list:
    """
    Query DuckDuckGo images and return a list of image URLs (may be empty).
    The function first fetches a vqd token then calls i.js with it.
    """
    results = []
    vqd = get_vqd_token(query)
    if not vqd:
        return results

    params = {
        "l": "us-en",
        "o": "json",
        "q": query,
        "vqd": vqd,
        "f": ",,,",  # filters (none)
        "p": "1"    # safe search: 1 (moderate) -- note: DDG provides p param
    }

    try:
        r = requests.get(DDG_IJS, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        # 'results' is usually present and each has 'image' and 'thumbnail'
        for item in data.get("results", [])[:max_results]:
            img = item.get("image") or item.get("thumbnail") or item.get("url")
            if img:
                results.append(img)
    except Exception as e:
        log.warning("DuckDuckGo image query failed for '%s': %s", query, e)

    return results

# ----------------------
# Helper to choose best image from results
# ----------------------
def choose_image_from_results(results: list) -> str | None:
    """
    Choose the first reasonable image URL from DuckDuckGo results.
    Returns None if none suitable.
    """
    if not results:
        return None
    # Prefer HTTPS and common image extensions
    for url in results:
        if isinstance(url, str) and url.startswith("http"):
            lower = url.lower()
            if any(lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                return url
    # fallback to first URL if nothing with extension
    return results[0]

# ----------------------
# Main Flask routes
# ----------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/results", methods=["POST"])
def results():
    """
    POST payload expected:
    { band: number, bust: number, activity: string, root: string }

    Returns:
    {
      product_name, size, cup_diff, band, bust,
      images: [front_url, side_url, closeup_url],
      store_urls: { amazon, flipkart, myntra }
    }
    """
    payload = request.get_json(silent=True) or {}
    try:
        band = float(payload.get("band", 78))
        bust = float(payload.get("bust", 90))
    except (ValueError, TypeError):
        band = 78.0
        bust = 90.0

    activity = payload.get("activity", "Daily / Casual")
    root = payload.get("root", "Narrow")

    # sizing logic
    diff = max(0, round(bust - band))
    cup = "A"
    if 12 <= diff < 14:
        cup = "B"
    elif 14 <= diff < 16:
        cup = "C"
    elif 16 <= diff < 18:
        cup = "D"
    elif diff >= 18:
        cup = "DD/E"

    # round band to nearest 5 for typical band sizes
    band_rounded = int(round(band / 5.0) * 5)
    size = f"{band_rounded}{cup}"
    product_name = f"Comfort {size} {activity} bra" if root != "Wide" else f"Full coverage {size} bra"

    cup_group = cup_group_from_diff(diff)
    activity_key = activity_key_name(activity)

    # Build image search queries (front, side, closeup)
    # Use queries tuned for product-only studio shots on pastel background
    base_query = f"{size} {activity_key} bra product studio pastel background"
    front_query = f"{base_query} front view product photo"
    side_query = f"{base_query} 3/4 side view product photo"
    close_query = f"{base_query} closeup fabric detail product photo"

    # Attempt to fetch images live (DuckDuckGo)
    front_imgs = duckduckgo_image_search(front_query)
    side_imgs = duckduckgo_image_search(side_query)
    close_imgs = duckduckgo_image_search(close_query)

    front_url = choose_image_from_results(front_imgs)
    side_url = choose_image_from_results(side_imgs)
    close_url = choose_image_from_results(close_imgs)

    # Fallback to public placeholders in static/images if search fails
    placeholder = "/static/images/p1.svg"
    images = [
        front_url or placeholder,
        side_url or placeholder,
        close_url or placeholder
    ]

    # Build store search URLs (simple queries)
    query_term = quote_plus(product_name)
    store_urls = {
        "amazon": f"https://www.amazon.in/s?k={query_term}",
        "flipkart": f"https://www.flipkart.com/search?q={query_term}",
        "myntra": f"https://www.myntra.com/search?q={query_term}"
    }

    response = {
        "product_name": product_name,
        "size": size,
        "cup_diff": diff,
        "band": band,
        "bust": bust,
        "images": images,
        "store_urls": store_urls
    }

    return jsonify(response)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    

from flask import Flask, render_template, request, jsonify
from urllib.parse import quote_plus
import os

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/results", methods=["POST"])
def results():
    """
    Expects JSON body: { "band": 78, "bust": 90, "activity": "Daily / Casual", "root": "Narrow" }
    Returns JSON containing product_name, band, bust, cup_diff, images (list), and store_urls dict.
    """
    data = request.get_json() or {}

    try:
        band = float(data.get("band", 78))
    except (TypeError, ValueError):
        band = 78.0

    try:
        bust = float(data.get("bust", 90))
    except (TypeError, ValueError):
        bust = 90.0

    activity = data.get("activity", "Daily / Casual")
    root = data.get("root", "Narrow")

    # Basic product naming heuristic - you can replace with real logic
    band_label = int(round(band / 1.0))  # adjust rounding if you want
    cup_diff = max(0, int(round(bust - band)))

    # Compose product name (simple placeholder)
    product_name = f"Comfort {band_label} — {activity}"

    # Build a query_term to search in store pages
    query_term = quote_plus(product_name)

    # Build store URLs (Indian lingerie brands first, then marketplaces)
    store_urls = {
        # Indian lingerie / direct brands
        "zivame": f"https://www.zivame.com/catalogsearch/result/?q={query_term}",
        "clovia": f"https://www.clovia.com/search/?q={query_term}",
        "shyaway": f"https://www.shyaway.com/catalogsearch/result/?q={query_term}",
        "enamor": f"https://www.enamor.co.in/search?q={query_term}",
        "amante": f"https://www.amantelingerie.com/search?q={query_term}",

        # Marketplaces
        "amazon": f"https://www.amazon.in/s?k={query_term}",
        "flipkart": f"https://www.flipkart.com/search?q={query_term}",
        "myntra": f"https://www.myntra.com/search?q={query_term}",
    }

    # images: empty or placeholder list (frontend will pick sample images if backend doesn't provide)
    images = []  # optionally you can add image URLs here

    response = {
        "product_name": product_name,
        "band": int(band),
        "bust": int(bust),
        "cup_diff": cup_diff,
        "images": images,
        "store_urls": store_urls,
    }

    return jsonify(response)


if __name__ == "__main__":
    # For local testing only. For production, use a proper server (gunicorn / Render defaults).
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    

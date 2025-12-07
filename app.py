# app.py
# Replace your current app.py with this file.
# Expects generated AI images placed in: static/images/ai/
# Filenames (example): model_casual_small_front.jpg, model_sports_medium_side.jpg, model_highimpact_large_closeup.jpg

import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, static_folder='static', template_folder='templates')


def cup_group_from_diff(diff: int) -> str:
    """
    Map cup-difference (bust - band) to a cup group.
    Adjust thresholds here as you need.
    """
    if diff < 14:
        return "small"   # A/B
    if 14 <= diff < 16:
        return "medium"  # C/D
    return "large"       # DD/E+


def activity_key_name(activity_label: str) -> str:
    """
    Map the frontend activity text to a simplified key used in file names.
    Add mappings if your frontend uses different labels.
    """
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


def static_file_exists(path_from_static_root: str) -> bool:
    """
    Check existence of a file under the Flask static folder.
    path_from_static_root should start with 'images/...' or similar (no leading slash).
    """
    static_root = app.static_folder  # e.g. /path/to/project/static
    full = os.path.join(static_root, path_from_static_root)
    return os.path.exists(full)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/results', methods=['POST'])
def results():
    """
    Expects JSON: { band: number, bust: number, activity: string, root: string }
    Returns JSON including images and store search links.
    """
    payload = request.get_json(silent=True) or {}
    try:
        band = float(payload.get('band', 78))
        bust = float(payload.get('bust', 90))
    except (ValueError, TypeError):
        band = 78.0
        bust = 90.0

    activity = payload.get('activity', 'Daily / Casual')
    root = payload.get('root', 'Narrow')

    # Basic sizing logic (can be replaced with your own)
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

    band_rounded = int(round(band / 5.0) * 5)
    size = f"{band_rounded}{cup}"
    product_name = f"Comfort {size} {activity} bra" if root != 'Wide' else f"Full coverage {size} bra"

    # Determine cup group & activity key for filenames
    cup_group = cup_group_from_diff(diff)  # "small" / "medium" / "large"
    activity_key = activity_key_name(activity)  # "casual" / "sports" / "highimpact"

    # Build expected AI image file paths (under static/images/ai/)
    ai_base_path = 'images/ai'  # relative to static folder
    desired_images = [
        os.path.join(ai_base_path, f"model_{activity_key}_{cup_group}_front.jpg"),
        os.path.join(ai_base_path, f"model_{activity_key}_{cup_group}_side.jpg"),
        os.path.join(ai_base_path, f"model_{activity_key}_{cup_group}_closeup.jpg"),
    ]

    # Validate files exist, otherwise fallback to known local placeholders
    fallback_placeholder = 'images/p1.svg'  # keep it in static/images/p1.svg
    returned_images = []
    for rel in desired_images:
        # rel is like 'images/ai/model_casual_small_front.jpg'
        if static_file_exists(rel):
            returned_images.append('/' + rel.replace(os.path.sep, '/'))  # convert to web path
        else:
            # try jpg and png variants (some generators may save png); attempt replacements
            alt_jpg = rel.replace('.jpg', '.png')
            if static_file_exists(alt_jpg):
                returned_images.append('/' + alt_jpg.replace(os.path.sep, '/'))
            else:
                returned_images.append('/' + fallback_placeholder)

    # Build store search URLs (simple search by product name)
    query_term = product_name.replace(" ", "+")
    store_urls = {
        'amazon': f'https://www.amazon.in/s?k={query_term}',
        'flipkart': f'https://www.flipkart.com/search?q={query_term}',
        'myntra': f'https://www.myntra.com/search?q={query_term}'
    }

    response = {
        'product_name': product_name,
        'size': size,
        'cup_diff': diff,
        'band': band,
        'bust': bust,
        'images': returned_images,
        'store_urls': store_urls
    }

    return jsonify(response)


if __name__ == '__main__':
    # On Render (or other PaaS) the PORT env var will be set automatically.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    

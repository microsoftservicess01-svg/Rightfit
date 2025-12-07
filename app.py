# app.py
# Replace your current app.py with this file.
# Expects AI-generated product images placed at:
# static/images/ai/model_{activity}_{cupgroup}_{view}.jpg
# e.g. static/images/ai/model_casual_small_front.jpg

import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, static_folder='static', template_folder='templates')


def cup_group_from_diff(diff: int) -> str:
    """
    Map cup-difference (bust - band) to a cup group.
    Adjust thresholds as needed.
    """
    if diff < 14:
        return "small"   # A/B
    if 14 <= diff < 16:
        return "medium"  # C/D
    return "large"       # DD/E+


def activity_key_name(activity_label: str) -> str:
    """
    Map the frontend activity text to simplified keys used in filenames.
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
    Check if a file exists under app.static_folder.
    path_from_static_root should be like 'images/ai/...'
    """
    full = os.path.join(app.static_folder, path_from_static_root)
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
        band = float(payload.get('band', 0))
        bust = float(payload.get('bust', 0))
    except (ValueError, TypeError):
        band = 0.0
        bust = 0.0

    activity = payload.get('activity', 'Daily / Casual')
    root = payload.get('root', 'Narrow')

    # Basic sizing logic
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
    cup_group = cup_group_from_diff(diff)  # "small"/"medium"/"large"
    activity_key = activity_key_name(activity)  # "casual"/"sports"/"highimpact"

    # expected base relative to static folder
    ai_base = 'images/ai'
    views = ['front', 'side', 'closeup']
    desired = [os.path.join(ai_base, f"model_{activity_key}_{cup_group}_{v}.jpg") for v in views]

    # Validate existence and allow png/svg fallbacks
    fallback_placeholder = 'images/p1.svg'
    returned_images = []
    for rel in desired:
        # Try .jpg (as provided), then .png, then .svg
        if static_file_exists(rel):
            returned_images.append('/' + rel.replace(os.path.sep, '/'))
            continue
        alt_png = rel.replace('.jpg', '.png')
        if static_file_exists(alt_png):
            returned_images.append('/' + alt_png.replace(os.path.sep, '/'))
            continue
        alt_svg = rel.replace('.jpg', '.svg')
        if static_file_exists(alt_svg):
            returned_images.append('/' + alt_svg.replace(os.path.sep, '/'))
            continue
        returned_images.append('/' + fallback_placeholder)

    # Build store search URLs
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    

# theme_utils.py

# Unified Fear Score Color Mapping
FEAR_COLOR_MAP = {
    "Low": "#4FC3F7",     # Blue
    "Medium": "#FFD54F",  # Yellow
    "High": "#EF5350"     # Red
}

def get_fear_category(score, threshold=0.75):
    """Return fear level category name based on score and threshold."""
    if score < 0.5:
        return "Low"
    elif score < threshold:
        return "Medium"
    else:
        return "High"

def get_fear_color(score, threshold=0.75):
    """Return the color hex code corresponding to the fear level."""
    category = get_fear_category(score, threshold)
    return FEAR_COLOR_MAP[category]

import unicodedata

def normalize_city_name(city: str) -> str:
    """
    Normalizes a city name for consistent database lookups.
    - Strips whitespace
    - Converts to lowercase
    - Removes unicode accents (e.g., 'Bogotá' -> 'bogota')
    """
    if not city:
        return ""
    
    city = city.strip().lower()
    # Normalize unicode to NFKD (decomposes characters into base + combining characters)
    # Then encode to ascii ignoring the combining characters, and decode back to string
    return unicodedata.normalize('NFKD', city).encode('ascii', 'ignore').decode('utf-8')

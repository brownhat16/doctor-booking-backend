from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def calculate_relevance_score(distance: float, rating: float, is_available_today: bool) -> float:
    """
    Calculate a relevance score for ranking doctors.
    Weights:
    - Distance: 40% (Inverse: closer is better)
    - Rating: 30% (Higher is better)
    - Availability: 30% (Available today is better)
    """
    # Normalize distance (assuming 10km is "far" enough to be 0 score)
    dist_score = max(0, 10 - distance) / 10
    
    # Normalize rating (0-5 scale)
    rating_score = rating / 5
    
    # Accessibility score
    avail_score = 1.0 if is_available_today else 0.0
    
    final_score = (dist_score * 0.4) + (rating_score * 0.3) + (avail_score * 0.3)
    return round(final_score, 2)

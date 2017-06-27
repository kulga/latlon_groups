import math

def distance(A, B):
    """
    Accepts two tuples (lat, long) of latitude and longitude
    To identify distances
    """

    a_lat, a_long = A
    b_lat, b_long = B

    x = (b_long - a_long) * math.cos((a_lat + b_lat) / 2)
    y = b_lat - a_lat
    distance = math.sqrt(x ** 2 + y ** 2) * 6371

    return distance

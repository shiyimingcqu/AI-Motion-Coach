from math import acos, degrees, hypot


Point = tuple[float, float]


def calculate_angle(first: Point, vertex: Point, third: Point) -> float:
    first_vector = (first[0] - vertex[0], first[1] - vertex[1])
    third_vector = (third[0] - vertex[0], third[1] - vertex[1])
    first_length = hypot(*first_vector)
    third_length = hypot(*third_vector)

    if first_length == 0 or third_length == 0:
        return 0.0

    cosine = (
        first_vector[0] * third_vector[0] + first_vector[1] * third_vector[1]
    ) / (first_length * third_length)
    cosine = max(-1.0, min(1.0, cosine))
    return degrees(acos(cosine))

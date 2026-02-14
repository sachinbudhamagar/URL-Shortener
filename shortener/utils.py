import random
import string


# Base62 encoding function
def base62_encode(num):
    """Convert number to base62 string"""
    if num == 0:
        return "0"

    base62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
    # base62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    result = ""
    while num > 0:
        result = base62[num % 62] + result
        num //= 62

    return result


def generate_short_code(url_id):
    """Generate short code from URL database ID"""
    return base62_encode(url_id)


# Alternative: Random code generation
def generate_random_code(length=6):
    """Generate random alphanumeric code"""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))

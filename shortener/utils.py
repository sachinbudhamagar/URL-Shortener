import random
import string
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


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


def generate_qr_code(url, size=10):
    """
    Generate QR code for given URL

    Args:
        url: The URL to encode
        size: QR code size (default 10)

    Returns:
        ContentFile object containing PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="White")

    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return ContentFile(buffer.read(), name="qr.png")

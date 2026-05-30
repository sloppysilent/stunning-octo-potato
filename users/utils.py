# users/utils.py
import io
import random

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw, ImageFont

AVATAR_COLORS = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#96CEB4",
    "#FFEAA7",
]


def generate_user_avatar(user):
    if not user.name:
        return

    colors = AVATAR_COLORS
    img = Image.new("RGB", (200, 200), color=random.choice(colors))
    draw = ImageDraw.Draw(img)

    initial = user.name[0].upper()

    try:
        font = ImageFont.truetype("arial.ttf", 100)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initial, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((200 - text_width) // 2, (200 - text_height) // 2)

    draw.text(position, initial, fill="white", font=font)

    img_io = io.BytesIO()
    img.save(img_io, format="PNG")
    img_io.seek(0)

    filename = f"avatar_{user.id}_{user.email}.png"
    user.avatar.save(filename, SimpleUploadedFile(filename, img_io.read()), save=True)

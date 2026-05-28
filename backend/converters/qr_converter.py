import os
import io
import logging
from typing import Optional

logger = logging.getLogger("hidconverter")

try:
    import qrcode
    from qrcode.image.svg import SvgImage
except ImportError:
    qrcode = None

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    from PIL import Image
except ImportError:
    pyzbar_decode = None


def encode_qr(text: str, output_path: str, fmt: str = "png") -> str:
    if qrcode is None:
        raise RuntimeError("Missing dependency: qrcode")

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)

    if fmt == "svg":
        img = qr.make_image(image_factory=SvgImage)
        img.save(output_path)
    else:
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)

    logger.info(f"QR code generated -> {output_path}")
    return output_path


def decode_qr(file_path: str) -> str:
    if pyzbar_decode is None:
        raise RuntimeError("Missing dependency: pyzbar (pip install pyzbar)")

    img = Image.open(file_path)
    results = pyzbar_decode(img)

    if not results:
        raise ValueError("No QR code found in the image")

    texts = []
    for res in results:
        text = res.data.decode("utf-8", errors="replace")
        texts.append(text)

    return "\n".join(texts)

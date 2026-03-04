import base64
import io
from typing import Tuple, Dict
from PIL import Image
from fastapi import HTTPException, UploadFile


ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_DIMENSION = 1920


def validate_image_file(file: UploadFile, max_size_mb: int) -> None:
    """Validate image file type and size."""

    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed types: JPG, PNG, WEBP"
        )

    # Read file to check size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename} exceeds maximum size of {max_size_mb}MB"
        )


def resize_if_needed(image: Image.Image) -> Image.Image:
    """Resize image if dimensions exceed MAX_DIMENSION while preserving aspect ratio."""
    width, height = image.size

    if width <= MAX_DIMENSION and height <= MAX_DIMENSION:
        return image

    # Calculate new dimensions
    if width > height:
        new_width = MAX_DIMENSION
        new_height = int((MAX_DIMENSION / width) * height)
    else:
        new_height = MAX_DIMENSION
        new_width = int((MAX_DIMENSION / height) * width)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def image_to_base64(image_bytes: bytes) -> Tuple[str, Dict[str, any]]:
    """Convert image bytes to base64 and extract metadata."""

    # Open image
    image = Image.open(io.BytesIO(image_bytes))

    # Extract metadata
    metadata = {
        "format": image.format,
        "mode": image.mode,
        "width": image.size[0],
        "height": image.size[1]
    }

    # Resize if needed
    image = resize_if_needed(image)

    # Convert to RGB if necessary (for PNG with alpha channel)
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
        image = background

    # Convert to bytes
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    image_bytes = buffer.getvalue()

    # Encode to base64
    base64_string = base64.b64encode(image_bytes).decode("utf-8")

    return base64_string, metadata


async def process_upload_file(file: UploadFile, max_size_mb: int) -> Tuple[bytes, Dict[str, any]]:
    """Process uploaded file: validate, read, and extract metadata."""

    validate_image_file(file, max_size_mb)

    # Read file content
    content = await file.read()

    # Convert to base64 and get metadata
    _, metadata = image_to_base64(content)
    metadata["filename"] = file.filename

    return content, metadata

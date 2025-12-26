import logging
import os
import re
import uuid
from datetime import datetime
from typing import Optional

import requests
from backend.utils.paths import get_app_data_dir
from fastapi import UploadFile
from sqlalchemy.orm import Session
from backend.data import crud, schemas

logger = logging.getLogger("janus_backend")


def _find_unique_filename(base_filename: str, image_dir: str) -> str:
    """
    Generate a unique filename by appending a counter if the file already exists.
    """
    filename_without_ext, file_extension = os.path.splitext(base_filename)

    pattern = r"^(.*?)(-\d+)?(-\d{2}-\d{2}-\d{2})?$"
    match = re.match(pattern, filename_without_ext)

    if match:
        description_part = match.group(1).rstrip("-")
        counter_part = int(match.group(2)[1:]) if match.group(2) else 0
        date_part = match.group(3)[1:] if match.group(3) else datetime.now().strftime("%d-%m-%y")
        base_name = description_part
    else:
        base_name = filename_without_ext
        counter_part = 0
        description_part = base_name
        date_part = ""

    counter = counter_part
    while True:
        if counter == 0:
            new_filename = f"{description_part}-{date_part}{file_extension}"
        else:
            new_filename = f"{description_part}-{counter}-{date_part}{file_extension}"

        if not os.path.exists(os.path.join(image_dir, new_filename)):
            return new_filename

        counter += 1
        if counter > 1000:
            return f"{base_name}-{uuid.uuid4()}{file_extension}"


def save_image_from_url(
    image_url: str, title: Optional[str] = None, subdirectory: Optional[str] = None
) -> Optional[str]:
    """
    Download an image from a URL and save it locally.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        base_image_dir = os.path.join(get_app_data_dir(), "images")
        image_dir = os.path.join(base_image_dir, subdirectory) if subdirectory else base_image_dir
        os.makedirs(image_dir, exist_ok=True)

        current_date = datetime.now().strftime("%d-%m-%y")
        if title:
            sanitized_title = title.replace(" ", "-")
            sanitized_title = re.sub(r"[^a-zA-Z0-9-]", "", sanitized_title).rstrip()
            base_filename = f"{sanitized_title}-{current_date}.png"
        else:
            base_filename = f"untitled-{current_date}.png"

        unique_filename = _find_unique_filename(base_filename, image_dir)
        file_path = os.path.join(image_dir, unique_filename)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if subdirectory:
            relative_path = f"/user_images/{subdirectory}/{unique_filename}"
        else:
            relative_path = f"/user_images/{unique_filename}"

        logger.debug(f"Image saved locally to {file_path}. Returning web path: {relative_path}")
        return relative_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return None


def save_image_from_bytes(
    image_bytes: bytes,
    description: str = "untitled",
    file_extension: str = "png",
    subdirectory: Optional[str] = None,
) -> str:
    """
    Save image data from bytes to a file.
    """
    base_image_dir = os.path.join(get_app_data_dir(), "images")
    image_dir = os.path.join(base_image_dir, subdirectory) if subdirectory else base_image_dir
    os.makedirs(image_dir, exist_ok=True)

    current_date = datetime.now().strftime("%d-%m-%y")
    sanitized_description = description.replace(" ", "-")
    sanitized_description = re.sub(r"[^a-zA-Z0-9-]", "", sanitized_description).rstrip()

    if len(sanitized_description) > 100:
        sanitized_description = sanitized_description[:100]

    filename = f"{sanitized_description}-{current_date}.{file_extension}"
    unique_filename = _find_unique_filename(filename, image_dir)
    file_path = os.path.join(image_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    logger.info(f"Image saved from bytes to {file_path}")

    if subdirectory:
        return f"/user_images/{subdirectory}/{unique_filename}"
    else:
        return f"/user_images/{unique_filename}"


async def migrate_image_paths(db_session, message_model) -> None:
    """
    Migrate image paths from external URLs to local paths.
    """
    logger.info("Starting image path migration...")
    messages_with_images = (
        db_session.query(message_model).filter(message_model.image_path.isnot(None)).all()
    )

    for message in messages_with_images:
        if message.image_path and message.image_path.startswith(
            "https://oaidalleapiprodscus.blob.core.windows.net"
        ):
            logger.debug(f"Migrating image for message ID {message.id} from URL.")
            new_path = save_image_from_url(message.image_path, subdirectory=None)
            if new_path:
                message.image_path = new_path
        else:
            logger.debug(
                f"Image path for message ID {message.id} is already local or not a DALL-E URL: {message.image_path}"
            )
    db_session.commit()
    logger.info("Image path migration complete.")


def rename_image_file(old_relative_path: str, new_filename_with_extension: str):
    """
    Benennt eine Bilddatei auf der Festplatte um.
    """
    base_image_dir = os.path.join(get_app_data_dir(), "images")
    
    cleaned_old_relative_path = old_relative_path.replace("user_images/", "", 1)
    
    old_absolute_path = os.path.join(base_image_dir, cleaned_old_relative_path)
    
    image_directory = os.path.dirname(cleaned_old_relative_path)
    new_absolute_path = os.path.join(base_image_dir, image_directory, new_filename_with_extension)

    logger.debug(f"Attempting to rename image from {old_absolute_path} to {new_absolute_path}")

    if not os.path.exists(old_absolute_path):
        raise FileNotFoundError(f"Die Datei {old_absolute_path} wurde nicht gefunden.")
    
    if os.path.exists(new_absolute_path):
        raise FileExistsError(f"Eine Datei mit dem Namen {new_filename_with_extension} existiert bereits im Zielverzeichnis.")

    os.rename(old_absolute_path, new_absolute_path)
    logger.info(f"Bild erfolgreich umbenannt: {old_absolute_path} -> {new_absolute_path}")


async def save_uploaded_file(db: Session, file: UploadFile) -> schemas.GeneratedImage:
    """
    Saves an uploaded image, creates a database entry, and returns the object.
    """
    contents = await file.read()
    
    original_filename = file.filename or "uploaded-image"
    filename_base, file_extension = os.path.splitext(original_filename)
    if not file_extension:
        file_extension = ".png"
        
    image_url = save_image_from_bytes(
        image_bytes=contents,
        description=filename_base,
        file_extension=file_extension.lstrip('.'),
        subdirectory="uploads"
    )

    image_data = schemas.GeneratedImageCreate(
        prompt=f"Uploaded: {original_filename}",
        provider="user_upload",
        model="local",
        parameters={},
        style_preset="N/A"
    )
    
    new_image_entry = crud.create_generated_image(
        db=db, 
        image_data=image_data, 
        image_url=image_url
    )
    
    new_image_entry.is_uploaded = True
    db.commit()
    db.refresh(new_image_entry)

    logger.info(f"User-uploaded image '{original_filename}' saved to '{image_url}' and logged in DB.")

    return new_image_entry
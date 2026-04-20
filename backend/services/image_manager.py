import logging
import os
import re
import random
import uuid
import hashlib
from datetime import datetime
from typing import Optional

import requests
from backend.utils.paths import get_images_dir
from fastapi import UploadFile
from sqlalchemy.orm import Session
import backend.data.models as models  # <--- NEW
from backend.utils.security_utils import secure_filename

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

        image_dir = os.path.join(get_images_dir(), subdirectory) if subdirectory else get_images_dir()
        os.makedirs(image_dir, exist_ok=True)

        current_date = datetime.now().strftime("%d-%m-%y")
        if title:
            sanitized_title = secure_filename(title) # Apply secure_filename here
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
    image_dir = os.path.join(get_images_dir(), subdirectory) if subdirectory else get_images_dir()
    os.makedirs(image_dir, exist_ok=True)

    # FIX: Dateinamen mit Mikrosekunden und Zufallszahl garantieren Eindeutigkeit
    timestamp = datetime.now().strftime("%d-%m-%y-%H-%M-%S-%f")
    random_suffix = random.randint(1000, 9999)
    
    # sanitized_description already comes from secure_filename, but we might want to do it again for good measure
    sanitized_description = secure_filename(description)
    
    if len(sanitized_description) > 50:  # Reduced from 100 to leave room for timestamp
        sanitized_description = sanitized_description[:50]
    
    filename = f"{sanitized_description}-{timestamp}-{random_suffix}.{file_extension}"
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
    # Remove the leading /user_images/ or user_images/ from the path
    cleaned_old_relative_path = old_relative_path.replace("/user_images/", "").replace("user_images/", "")
    
    # Get the full path to the old file in the new location
    old_absolute_path = os.path.join(get_images_dir(), cleaned_old_relative_path)
    
    # Create the new path in the same directory with the new filename
    image_directory = os.path.dirname(old_absolute_path)
    new_absolute_path = os.path.join(image_directory, secure_filename(new_filename_with_extension))

    logger.debug(f"Attempting to rename image from {old_absolute_path} to {new_absolute_path}")

    if not os.path.exists(old_absolute_path):
        raise FileNotFoundError(f"Die Datei {old_absolute_path} wurde nicht gefunden.")
    
    if os.path.exists(new_absolute_path):
        raise FileExistsError(f"Eine Datei mit dem Namen {new_filename_with_extension} existiert bereits im Zielverzeichnis.")

    os.rename(old_absolute_path, new_absolute_path)
    logger.info(f"Bild erfolgreich umbenannt: {old_absolute_path} -> {new_absolute_path}")


def _calculate_file_hash(contents: bytes) -> str:
    """Calculate SHA-256 hash of file contents."""
    return hashlib.sha256(contents).hexdigest()

async def save_uploaded_file(db: Session, file: UploadFile) -> models.GeneratedImage:
    # 1. Inhalt lesen für Hash
    content = await file.read()
    sha256_hash = hashlib.sha256(content).hexdigest()
    
    # 2. Prüfen, ob Hash existiert
    existing_image = db.query(models.GeneratedImage).filter(
        models.GeneratedImage.content_hash == sha256_hash,
        models.GeneratedImage.is_uploaded == True
    ).first()
    
    if existing_image:
        # Prüfen, ob die physische Datei auch noch da ist
        # FIX: Sauberer Replace statt lstrip, um Pfadfehler (\uploads) zu vermeiden
        relative_path = existing_image.image_url.replace("/user_images/", "", 1)
        # Windows-Slashes sicherstellen
        relative_path = relative_path.replace("/", os.sep)
        full_path = os.path.join(get_images_dir(), relative_path)
        
        if os.path.exists(full_path):
            logger.info(f"Duplicate upload detected (Hash: {sha256_hash}). Reuse existing ID {existing_image.id}")
            return existing_image
        else:
            logger.warning(f"DB entry exists for hash {sha256_hash}, but file is missing at {full_path}. Re-saving.")

    # 3. Wenn nicht existiert (oder Datei fehlt): Neu speichern
    # Wir müssen den Pointer im File-Objekt zurücksetzen, da wir schon gelesen haben?
    # Nein, wir haben den Content ja schon in der Variable 'content'.
    # Wir rufen save_image_from_bytes aber normalerweise mit Bytes auf.
    
    # Da save_image_from_bytes einen eindeutigen Namen generiert, nutzen wir das.
    # ABER: Wir wollen, dass es im 'uploads' Ordner landet.
    
    # Manuelle Speicher-Logik für Uploads (um save_image_from_bytes nicht zu komplizieren)
    import random
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%d-%m-%y-%H-%M-%S-%f")
    random_suffix = random.randint(1000, 9999)
    # Behalte Original-Extension
    ext = os.path.splitext(file.filename)[1]
    if not ext: ext = ".png"
    
    # Wir nehmen den Original-Dateinamen als Basis, aber machen ihn unique
    safe_filename = os.path.splitext(file.filename)[0][:30] # Kürzen
    # Bereinigen
    import re
    safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '', safe_filename)
    
    unique_filename = f"{safe_filename}-{timestamp}-{random_suffix}{ext}"
    
    uploads_dir = os.path.join(get_images_dir(), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_path = os.path.join(uploads_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    logger.info(f"Image saved from bytes to {file_path}")

    # 4. DB Eintrag
    relative_url = f"/user_images/uploads/{unique_filename}"
    
    # FIX: Nur existierende Spalten verwenden!
    new_image = models.GeneratedImage(
        image_url=relative_url,
        prompt=file.filename,  # Dateiname als Prompt-Ersatz
        is_uploaded=True,
        content_hash=sha256_hash
    )
    
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    logger.info(f"User-uploaded image '{file.filename}' saved to '{relative_url}'")
    return new_image
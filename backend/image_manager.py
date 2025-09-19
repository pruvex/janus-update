import re
import os
import uuid
import requests
import logging
from datetime import datetime
from typing import Optional
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

def _find_unique_filename(base_filename: str, image_dir: str) -> str:
    """
    Generate a unique filename by appending a counter if the file already exists.
    
    Args:
        base_filename: The base filename to use
        image_dir: Directory where the image will be saved
        
    Returns:
        A unique filename that doesn't exist in the target directory
    """
    filename_without_ext, file_extension = os.path.splitext(base_filename)
    
    pattern = r'^(.*?)(-\d+)?(-\d{2}-\d{2}-\d{2})?$'
    match = re.match(pattern, filename_without_ext)
    
    if match:
        description_part = match.group(1).rstrip('-')
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

def save_image_from_url(image_url: str, title: Optional[str] = None, subdirectory: Optional[str] = None) -> Optional[str]:
    """
    Download an image from a URL and save it locally.
    
    Args:
        image_url: URL of the image to download.
        title: Optional title for the filename.
        subdirectory: Optional subfolder within the main images directory.
        
    Returns:
        Web-accessible path to the saved image, or None if download failed.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        base_image_dir = os.path.join(get_app_data_dir(), "images")
        image_dir = os.path.join(base_image_dir, subdirectory) if subdirectory else base_image_dir
        os.makedirs(image_dir, exist_ok=True)
        
        current_date = datetime.now().strftime("%d-%m-%y")
        if title:
            sanitized_title = title.replace(' ', '-')
            sanitized_title = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_title).rstrip()
            base_filename = f"{sanitized_title}-{current_date}.png"
        else:
            base_filename = f"untitled-{current_date}.png"
        
        unique_filename = _find_unique_filename(base_filename, image_dir)
        file_path = os.path.join(image_dir, unique_filename)

        with open(file_path, 'wb') as f:
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

def save_image_from_bytes(image_bytes: bytes, description: str = "untitled", file_extension: str = "png", subdirectory: Optional[str] = None) -> str:
    """
    Save image data from bytes to a file.
    
    Args:
        image_bytes: Raw image data as bytes.
        description: Description for the filename.
        file_extension: File extension to use.
        subdirectory: Optional subfolder within the main images directory.
        
    Returns:
        Web-accessible path to the saved image.
    """
    base_image_dir = os.path.join(get_app_data_dir(), "images")
    image_dir = os.path.join(base_image_dir, subdirectory) if subdirectory else base_image_dir
    os.makedirs(image_dir, exist_ok=True)

    current_date = datetime.now().strftime("%d-%m-%y")
    sanitized_description = description.replace(' ', '-')
    sanitized_description = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_description).rstrip()

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
    messages_with_images = db_session.query(message_model).filter(message_model.image_path.isnot(None)).all()
    
    for message in messages_with_images:
        if message.image_path and message.image_path.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
            logger.debug(f"Migrating image for message ID {message.id} from URL.")
            # For migration, we save to the root image folder, not a subfolder.
            new_path = save_image_from_url(message.image_path, subdirectory=None)
            if new_path:
                message.image_path = new_path
        else:
            logger.debug(f"Image path for message ID {message.id} is already local or not a DALL-E URL: {message.image_path}")
    db_session.commit()
    logger.info("Image path migration complete.")

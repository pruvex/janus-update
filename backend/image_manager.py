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
    
    # First, check if the filename already has a counter and date pattern we can extract
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
    
    # Find a unique filename by appending a counter if needed
    counter = counter_part
    while True:
        if counter == 0:
            new_filename = f"{description_part}-{date_part}{file_extension}"
        else:
            new_filename = f"{description_part}-{counter}-{date_part}{file_extension}"
        
        if not os.path.exists(os.path.join(image_dir, new_filename)):
            return new_filename
            
        counter += 1
        if counter > 1000:  # Safety check to prevent infinite loops
            # If we can't find a unique name, append a UUID
            return f"{base_name}-{uuid.uuid4()}{file_extension}"


def save_image_from_url(image_url: str, title: Optional[str] = None) -> Optional[str]:
    """
    Download an image from a URL and save it locally with a descriptive name.
    
    Args:
        image_url: URL of the image to download
        title: Optional title to use in the filename
        
    Returns:
        Web-accessible path to the saved image, or None if download failed
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        image_dir = os.path.join(get_app_data_dir(), "images")
        os.makedirs(image_dir, exist_ok=True)
        
        # Generate filename based on title and date
        current_date = datetime.now().strftime("%d-%m-%y")
        if title:
            sanitized_title = title.replace(' ', '-')
            sanitized_title = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_title).rstrip()
            base_filename = f"{sanitized_title}-{current_date}.png"
        else:
            base_filename = f"untitled-{current_date}.png"
        
        # Find a unique filename
        unique_filename = _find_unique_filename(base_filename, image_dir)
        file_path = os.path.join(image_dir, unique_filename)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        relative_path = f"/user_images/{unique_filename}"
        logger.debug(f"Image saved locally to {file_path}. Returning web path: {relative_path}")
        return relative_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return None


def save_image_from_bytes(image_bytes: bytes, description: str = "untitled", file_extension: str = "png") -> str:
    """
    Save image data from bytes to a file with a descriptive name.
    
    Args:
        image_bytes: Raw image data as bytes
        description: Description to use in the filename
        file_extension: File extension to use (without the dot)
        
    Returns:
        Web-accessible path to the saved image
    """
    image_dir = os.path.join(get_app_data_dir(), "images")
    os.makedirs(image_dir, exist_ok=True)

    current_date = datetime.now().strftime("%d-%m-%y")
    sanitized_description = description.replace(' ', '-')
    sanitized_description = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_description).rstrip()

    filename = f"{sanitized_description}-{current_date}.{file_extension}"
    # Find a unique filename
    unique_filename = _find_unique_filename(filename, image_dir)
    file_path = os.path.join(image_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    logger.info(f"Image saved from bytes to {file_path}")
    return f"/user_images/{unique_filename}"


async def migrate_image_paths(db_session, message_model) -> None:
    """
    Migrate image paths from external URLs to local paths.
    
    This function scans all messages with image paths and migrates any external
    DALL-E image URLs to local file paths.
    
    Args:
        db_session: Database session
        message_model: Message model class
    """
    logger.info("Starting image path migration...")
    messages_with_images = db_session.query(message_model).filter(message_model.image_path.isnot(None)).all()
    
    for message in messages_with_images:
        if message.image_path and message.image_path.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
            logger.debug(f"Migrating image for message ID {message.id} from URL.")
            new_path = save_image_from_url(message.image_path)
            if new_path:
                message.image_path = new_path
        else:
            logger.debug(f"Image path for message ID {message.id} is already local or not a DALL-E URL: {message.image_path}")
    
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    logger.info(f"Image saved from bytes to {file_path}")
    return f"/user_images/{unique_filename}"


from datetime import datetime

def save_image_from_url(image_url: str, title: str = None) -> str:
    """Downloads an image from a URL, saves it locally with a descriptive name, and returns the web-accessible path."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        image_dir = os.path.join(get_app_data_dir(), "images")
        os.makedirs(image_dir, exist_ok=True)
        
        # Generate filename based on title and date
        current_date = datetime.now().strftime("%d-%m-%y")
        if title:
            sanitized_title = title.replace(' ', '-')
            sanitized_title = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_title).rstrip()
            base_filename = f"{sanitized_title}-{current_date}.png"
        else:
            base_filename = f"untitled-{current_date}.png"
        
        # Find a unique filename
        unique_filename = _find_unique_filename(base_filename, image_dir)
        file_path = os.path.join(image_dir, unique_filename)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        relative_path = f"/user_images/{unique_filename}"
        logger.debug(f"Image saved locally to {file_path}. Returning web path: {relative_path}")
        return relative_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return None

# (Die Funktion migrate_image_paths bleibt unverändert)
async def migrate_image_paths(db_session, message_model):
    logger.info("Starting image path migration...")
    messages_with_images = db_session.query(message_model).filter(message_model.image_path.isnot(None)).all()
    for message in messages_with_images:
        if message.image_path and message.image_path.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
            logger.debug(f"Migrating image for message ID {message.id} from URL.")
            new_path = save_image_from_url(message.image_path)
            if new_path:
                message.image_path = new_path
        else:
            logger.debug(f"Image path for message ID {message.id} is already local or not a DALL-E URL: {message.image_path}")
    db_session.commit()
    logger.info("Image path migration complete.")

# (Ihre neue Funktion 'save_image_from_bytes' sollte bereits so aussehen)
def save_image_from_bytes(image_bytes: bytes, description: str = "untitled", file_extension: str = "png") -> str:
    """Saves image data from bytes to a file with a descriptive name and returns the web-accessible path."""
    image_dir = os.path.join(get_app_data_dir(), "images")
    os.makedirs(image_dir, exist_ok=True)

    current_date = datetime.now().strftime("%d-%m-%y")
    sanitized_description = description.replace(' ', '-')
    sanitized_description = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_description).rstrip()

    filename = f"{sanitized_description}-{current_date}.{file_extension}"
    # Find a unique filename
    unique_filename = _find_unique_filename(filename, image_dir)
    file_path = os.path.join(image_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    logger.info(f"Image saved from bytes to {file_path}")
    return f"/user_images/{unique_filename}"


from datetime import datetime

def save_image_from_url(image_url: str, title: str = None) -> str:
    """Downloads an image from a URL, saves it locally with a descriptive name, and returns the web-accessible path."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        image_dir = os.path.join(get_app_data_dir(), "images")
        os.makedirs(image_dir, exist_ok=True)
        
        # Generate filename based on title and date
        current_date = datetime.now().strftime("%d-%m-%y")
        if title:
            sanitized_title = title.replace(' ', '-')
            sanitized_title = re.sub(r'[^a-zA-Z0-9-]', '', sanitized_title).rstrip()
            base_filename = f"{sanitized_title}-{current_date}.png"
        else:
            base_filename = f"untitled-{current_date}.png"
        
        # Find a unique filename
        unique_filename = _find_unique_filename(base_filename, image_dir)
        file_path = os.path.join(image_dir, unique_filename)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        relative_path = f"/user_images/{unique_filename}"
        logger.debug(f"Image saved locally to {file_path}. Returning web path: {relative_path}")
        return relative_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return None

# (Die Funktion migrate_image_paths bleibt unverändert)
async def migrate_image_paths(db_session, message_model):
    logger.info("Starting image path migration...")
    messages_with_images = db_session.query(message_model).filter(message_model.image_path.isnot(None)).all()
    for message in messages_with_images:
        if message.image_path and message.image_path.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
            logger.debug(f"Migrating image for message ID {message.id} from URL.")
            new_path = save_image_from_url(message.image_path)
            if new_path:
                message.image_path = new_path
        else:
            logger.debug(f"Image path for message ID {message.id} is already local or not a DALL-E URL: {message.image_path}")
    db_session.commit()
    logger.info("Image path migration complete.")
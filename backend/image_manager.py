import re
import os
import uuid
import requests
import logging
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

def _find_unique_filename(base_filename: str, image_dir: str) -> str:
    filename_without_ext, file_extension = os.path.splitext(base_filename)
    counter = 0
    unique_filename = base_filename
    while os.path.exists(os.path.join(image_dir, unique_filename)):
        counter += 1
        unique_filename = f"{filename_without_ext}-{counter}{file_extension}"
    return unique_filename

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
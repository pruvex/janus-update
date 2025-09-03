import os
import uuid
import requests
import logging
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

# (Ihre neue Funktion 'save_image_from_bytes' sollte bereits so aussehen)
def save_image_from_bytes(image_bytes: bytes, filename: str = None) -> str:
    """Saves image data from bytes to a file and returns the web-accessible path."""
    image_dir = os.path.join(get_app_data_dir(), "images")
    os.makedirs(image_dir, exist_ok=True)
    
    if filename is None:
        filename = f"{uuid.uuid4()}.png"
    
    file_path = os.path.join(image_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(image_bytes)
        
    logger.info(f"Image saved from bytes to {file_path}")
    # Gibt den Pfad zurück, den das Frontend verwenden kann
    return f"/user_images/{filename}"


def save_image_from_url(image_url: str) -> str:
    """Downloads an image from a URL, saves it locally, and returns the web-accessible path."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        image_dir = os.path.join(get_app_data_dir(), "images")
        os.makedirs(image_dir, exist_ok=True)
        
        filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(image_dir, filename)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # --- KORREKTUR HIER ---
        # Gibt jetzt direkt den korrekten, vom Server bereitgestellten Pfad zurück.
        relative_path = f"/user_images/{filename}"
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
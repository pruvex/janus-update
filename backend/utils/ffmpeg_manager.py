import os
import platform
import requests
import zipfile
from tqdm import tqdm
import appdirs
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger("janus_backend.ffmpeg")

# URL to a trusted, compact FFmpeg build
# Using ffbinaries prebuilt releases
FFMPEG_BASE_URL = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/"
FFMPEG_VERSION = "6.1"

def get_platform_suffix() -> str:
    """Get the platform-specific suffix for FFmpeg binaries."""
    system = platform.system().lower()
    if system == 'windows':
        return 'win-64'
    elif system == 'darwin':
        return 'osx-64' if platform.machine() == 'x86_64' else 'osx-arm64'
    else:  # linux
        return 'linux-64'

def get_ffmpeg_url() -> str:
    """Get the download URL for FFmpeg based on the current platform."""
    platform_suffix = get_platform_suffix()
    return f"{FFMPEG_BASE_URL}ffmpeg-{FFMPEG_VERSION}-{platform_suffix}.zip"

def get_app_data_dir() -> str:
    """Get the application data directory for Janus."""
    return appdirs.user_data_dir("Janus", "Janus-Projekt")

def get_ffmpeg_dir() -> str:
    """Get the directory where FFmpeg should be stored."""
    return os.path.join(get_app_data_dir(), "ffmpeg")

def get_ffmpeg_path() -> Optional[str]:
    """
    Ensure FFmpeg is available, download it if necessary, and return the path to ffmpeg.
    
    Returns:
        str: Path to the ffmpeg executable, or None if download/initialization failed.
    """
    # Determine the correct binary name based on the platform
    binary_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    
    # Set up paths
    ffmpeg_dir = get_ffmpeg_dir()
    ffmpeg_path = os.path.join(ffmpeg_dir, binary_name)
    
    # Check if FFmpeg already exists
    if os.path.isfile(ffmpeg_path):
        logger.info(f"FFmpeg found at: {ffmpeg_path}")
        return ffmpeg_path
    
    # Create the directory if it doesn't exist
    os.makedirs(ffmpeg_dir, exist_ok=True)
    
    # Download FFmpeg
    download_url = get_ffmpeg_url()
    zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
    
    try:
        logger.info(f"FFmpeg not found. Downloading from {download_url}...")
        
        # Download with progress bar
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_path, 'wb') as f, tqdm(
            desc="Downloading FFmpeg",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
        
        logger.info("Download complete. Extracting...")
        
        # Extract the archive
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        
        # Clean up the zip file
        os.remove(zip_path)
        
        # On Windows, ensure the executable has the .exe extension
        if platform.system() == "Windows" and not ffmpeg_path.endswith('.exe'):
            if os.path.exists(ffmpeg_path):
                os.rename(ffmpeg_path, ffmpeg_path + ".exe")
                ffmpeg_path += ".exe"
        
        # Make the binary executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(ffmpeg_path, 0o755)
        
        if os.path.isfile(ffmpeg_path):
            logger.info(f"FFmpeg successfully installed to: {ffmpeg_path}")
            return ffmpeg_path
        else:
            raise FileNotFoundError("FFmpeg binary not found after extraction")
    
    except Exception as e:
        logger.error(f"Error downloading/setting up FFmpeg: {e}")
        # Clean up in case of error
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass
        return None

def ensure_ffmpeg() -> bool:
    """
    Ensure FFmpeg is available and set up for pydub and other libraries.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise.
    """
    try:
        # Get FFmpeg path (will download if needed)
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path or not os.path.isfile(ffmpeg_path):
            logger.error("Failed to set up FFmpeg")
            return False
        
        # Get the directory containing FFmpeg
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        
        # Add to PATH for libraries that search for FFmpeg in PATH
        if ffmpeg_dir not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
            logger.info(f"Added FFmpeg directory to PATH: {ffmpeg_dir}")
        
        # Set up pydub to use our FFmpeg
        try:
            from pydub import AudioSegment
            AudioSegment.ffmpeg = ffmpeg_path
            
            # Also set ffprobe if available
            ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe" + ('.exe' if platform.system() == "Windows" else ""))
            if os.path.isfile(ffprobe_path):
                AudioSegment.ffprobe = ffprobe_path
                
            logger.info("FFmpeg configured for pydub")
        except ImportError:
            logger.warning("pydub not available, FFmpeg setup for pydub skipped")
        
        return True
    
    except Exception as e:
        logger.error(f"Error ensuring FFmpeg is available: {e}")
        return False

# Initialize FFmpeg when this module is imported
# This will download FFmpeg on first import if needed
# and set up the environment for pydub and other libraries
_ = ensure_ffmpeg()

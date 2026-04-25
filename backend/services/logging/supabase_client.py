"""
Thread-safe singleton Supabase client for logging pipeline.
Loads credentials from environment variables.
"""
import os
from pathlib import Path
from threading import Lock
from supabase import create_client, Client
from dotenv import load_dotenv

# Search for .env in the backend directory
# We know: File is in backend/services/logging/
# We need: backend/.env
base_path = Path(__file__).resolve().parent.parent.parent  # Lands in /backend/
env_path = base_path / ".env"

load_dotenv(dotenv_path=env_path)

# PFLICHT-LOGGING FÜR DAS TERMINAL (WICHTIG!)
print(f"--- LOGGING DEBUG ---")
print(f"Checking for .env at: {env_path}")
print(f"File exists: {env_path.exists()}")
print(f"SUPABASE_URL is set: {'YES' if os.getenv('SUPABASE_URL') else 'NO'}")
print(f"---------------------")


class SupabaseClientSingleton:
    """
    Thread-safe singleton for Supabase client.
    Ensures only one client instance exists across the application.
    """
    _instance: Client = None
    _lock: Lock = Lock()
    _initialized: bool = False

    def __new__(cls) -> Client:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    supabase_url = os.getenv("SUPABASE_URL")
                    supabase_key = os.getenv("SUPABASE_KEY")

                    if not supabase_url:
                        raise ValueError("SUPABASE_URL environment variable is not set")
                    if not supabase_key:
                        raise ValueError("SUPABASE_KEY environment variable is not set")

                    cls._instance = create_client(supabase_url, supabase_key)
                    cls._initialized = True

        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the singleton has been initialized."""
        return cls._initialized

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance.
        Primarily used for testing purposes.
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False


def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    
    Returns:
        Client: The Supabase client singleton instance.
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY environment variables are not set.
    """
    return SupabaseClientSingleton()

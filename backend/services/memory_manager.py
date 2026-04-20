"""DEPRECATED: Import from backend.services.memory instead."""
# Legacy: Tests und Patches erwarten vector_service / models / memory_cache auf diesem Modul.
import backend.data.models as models  # noqa: F401
from backend.services import vector_service  # noqa: F401
from backend.services.memory import *  # noqa: F401, F403
from backend.services.memory_cache import memory_cache  # noqa: F401

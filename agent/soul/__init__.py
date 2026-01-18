from .soul import Soul
from .soul_service import SoulService

# Create a global instance of the singleton
soul_service = SoulService()

__all__ = ['Soul', 'SoulService', 'soul_service']
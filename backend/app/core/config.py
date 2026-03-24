# Canonical import path for settings.
# Existing code using `from app.config import settings` continues to work.
# New code should use `from app.core.config import settings`.
from app.config import settings

__all__ = ["settings"]

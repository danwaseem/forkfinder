"""
Dependency injection helpers.

All FastAPI route dependencies should be imported from here.
This is the single place to find every injectable dependency in the project.

Usage in a router:
    from app.api.deps import get_db, get_current_user, require_owner, require_user

    @router.get("/me")
    def me(db: Session = Depends(get_db), user = Depends(get_current_user)):
        ...

    @router.post("/restaurants")
    def create(user = Depends(require_owner)):
        ...

    @router.post("/reviews")
    def write_review(user = Depends(require_user)):
        ...
"""

from app.database import get_db
from app.utils.auth import get_current_user, get_optional_user, require_owner, require_user

__all__ = ["get_db", "get_current_user", "get_optional_user", "require_owner", "require_user"]

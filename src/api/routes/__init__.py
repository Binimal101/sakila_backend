"""Package router registration.

This module imports each route submodule and includes their `router` on the
package-level `router` defined in `src/api/__init__.py`.
"""

from .. import router as package_router

# Import submodules (they expose `router` variables)
from . import health, users, films  # noqa: F401

# Include their routers onto the package-level router
package_router.include_router(health.router)
package_router.include_router(users.router)
package_router.include_router(films.router)

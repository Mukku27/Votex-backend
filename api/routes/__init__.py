"""
Routes subpackage: holds individual endpoint modules.
"""
from .root import router as root_router
from .report import router as report_router

__all__ = [
    "root_router",
    "report_router",
]

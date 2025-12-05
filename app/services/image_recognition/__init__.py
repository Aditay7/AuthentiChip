"""
Image Recognition Service Module

This module provides IC chip image recognition functionality using vision models.
"""

from .pipeline import extract_text_from_image, parse_ic_markings

__all__ = [
    "extract_text_from_image",
    "parse_ic_markings",
]

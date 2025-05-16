"""Package initialization file for cursor_detection"""
# This file makes the cursor_detection directory a Python package
# It's necessary for proper imports between the modules

from .cursor_detection import detect_cursor_state, load_templates, get_cursor_confidence
from .cursor_types import (
    detect_prohibited, 
    detect_red_sword, 
    detect_hand, 
    load_cursor_templates, 
    detect_cursor_by_template
)

# Explicitly define what gets imported with "from cursor_detection import *"
__all__ = [
    'detect_cursor_state',
    'load_templates',
    'get_cursor_confidence',
    'detect_prohibited',
    'detect_red_sword',
    'detect_hand',
    'load_cursor_templates',
    'detect_cursor_by_template'
]
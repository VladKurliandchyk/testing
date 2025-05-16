"""Base cursor detection module - core functionality"""
import cv2
import numpy as np
import time
import os
from collections import Counter

# Debug settings
DEBUG_FOLDER = "cursor_debug"
DEBUG = False  # Set to True for debugging

if DEBUG and not os.path.exists(DEBUG_FOLDER):
    os.makedirs(DEBUG_FOLDER)


def detect_cursor_state(frame, target_x, target_y, search_radius=50):
    """
    Accurately detect the cursor state around the target coordinates.
    
    Args:
        frame: Input frame (BGR format)
        target_x: X coordinate of target
        target_y: Y coordinate of target
        search_radius: Search area radius around target
        
    Returns:
        str: One of "RED_SWORD", "HAND", "PROHIBITED", "NONE"
    """
    # Define search area
    h, w = frame.shape[:2]
    x1 = max(0, target_x - search_radius)
    y1 = max(0, target_y - search_radius)
    x2 = min(w, target_x + search_radius)
    y2 = min(h, target_y + search_radius)
    
    # Extract ROI
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0 or roi.shape[0] == 0 or roi.shape[1] == 0:
        return "NONE"
    
    # Detect each cursor type
    from .cursor_types import detect_prohibited, detect_red_sword, detect_hand
    
    # Check for prohibited sign first (highest priority)
    if detect_prohibited(roi):
        return "PROHIBITED"
    
    # Get pixel counts for sword and hand
    sword_pixels = detect_red_sword(roi)
    hand_pixels = detect_hand(roi)
    
    # Decision logic
    if sword_pixels > 35:
        if hand_pixels > 25:
            # If both detected, prioritize sword if more dominant
            if sword_pixels > hand_pixels * 0.6:
                return "RED_SWORD"  
            else:
                return "HAND"
        return "RED_SWORD"
    elif hand_pixels > 25:
        return "HAND"
    else:
        return "NONE"


def get_cursor_confidence(frame, target_x, target_y, search_radius=50, num_samples=5):
    """
    Get cursor state with confidence by taking multiple samples.
    
    Returns:
        tuple: (state, confidence) where confidence is 0-1
    """
    states = []
    
    for i in range(num_samples):
        state = detect_cursor_state(frame, target_x, target_y, search_radius)
        states.append(state)
        if i < num_samples - 1:
            time.sleep(0.01)  # Small delay between samples
    
    # Count occurrences
    state_counts = Counter(states)
    most_common = state_counts.most_common(1)[0]
    confidence = most_common[1] / num_samples
    
    return most_common[0], confidence
"""Cursor type detection functions"""
import cv2
import numpy as np
import os


def detect_prohibited(roi):
    """
    Detect the red prohibition sign (circle with diagonal line).
    
    Args:
        roi: Region of interest in BGR format
        
    Returns:
        bool: True if prohibited sign detected
    """
    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Red color ranges
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # Create red mask
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Clean up mask
    kernel = np.ones((3,3), np.uint8)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 80:  # Minimum area threshold
            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.6:
                    # Check aspect ratio
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    if 0.7 < aspect_ratio < 1.3 and w > 10 and h > 10:
                        return True
    
    return False


def detect_red_sword(roi):
    """
    Detect the red sword cursor.
    
    Args:
        roi: Region of interest in BGR format
        
    Returns:
        int: Number of sword pixels detected
    """
    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Bright red color ranges for sword
    lower_sword_red1 = np.array([0, 140, 160])
    upper_sword_red1 = np.array([10, 255, 255])
    lower_sword_red2 = np.array([170, 140, 160])
    upper_sword_red2 = np.array([180, 255, 255])
    
    # Create sword mask
    mask_sword1 = cv2.inRange(hsv, lower_sword_red1, upper_sword_red1)
    mask_sword2 = cv2.inRange(hsv, lower_sword_red2, upper_sword_red2)
    mask_sword = cv2.bitwise_or(mask_sword1, mask_sword2)
    
    # Clean up mask
    sword_kernel = np.ones((2,2), np.uint8)
    mask_sword = cv2.morphologyEx(mask_sword, cv2.MORPH_CLOSE, sword_kernel)
    mask_sword = cv2.morphologyEx(mask_sword, cv2.MORPH_OPEN, sword_kernel)
    
    return cv2.countNonZero(mask_sword)


def detect_hand(roi):
    """
    Detect the hand cursor (skin tone colors).
    
    Args:
        roi: Region of interest in BGR format
        
    Returns:
        int: Number of hand pixels detected
    """
    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Skin tone color ranges
    lower_hand1 = np.array([10, 30, 80])   # Orange tones
    upper_hand1 = np.array([25, 140, 220])
    lower_hand2 = np.array([20, 25, 100])  # Yellowish/skin tone
    upper_hand2 = np.array([30, 130, 230])
    
    # Create hand mask
    mask_hand1 = cv2.inRange(hsv, lower_hand1, upper_hand1)
    mask_hand2 = cv2.inRange(hsv, lower_hand2, upper_hand2)
    mask_hand = cv2.bitwise_or(mask_hand1, mask_hand2)
    
    # Clean up mask
    hand_kernel = np.ones((2,2), np.uint8)
    mask_hand = cv2.morphologyEx(mask_hand, cv2.MORPH_CLOSE, hand_kernel)
    mask_hand = cv2.morphologyEx(mask_hand, cv2.MORPH_OPEN, hand_kernel)
    
    return cv2.countNonZero(mask_hand)


def load_cursor_templates(templates_dir=None):
    """
    Load cursor template images from the templates directory.
    
    Args:
        templates_dir: Directory containing cursor template images
        
    Returns:
        dict: Dictionary of template images
    """
    templates = {}
    
    # Default templates directory if not provided
    if templates_dir is None:
        # Try to resolve from current file location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
    
    if os.path.exists(templates_dir):
        template_files = {
            "RED_SWORD": "unfriendlyattack.png",
            "PROHIBITED": "dead.png",
            "HAND": "itempickup.png"
        }
        
        for cursor_type, filename in template_files.items():
            path = os.path.join(templates_dir, filename)
            if os.path.exists(path):
                templates[cursor_type] = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            else:
                if os.path.exists(templates_dir):
                    print(f"Template file not found: {path}")
                
    else:
        print(f"Templates directory not found: {templates_dir}")
                
    return templates


def detect_cursor_by_template(roi, templates):
    """
    Detect cursor by template matching.
    
    Args:
        roi: Region of interest in BGR format
        templates: Dictionary of template images
        
    Returns:
        str: Cursor type with highest matching score
    """
    best_match = "NONE"
    best_score = 0
    
    for cursor_type, template in templates.items():
        if template is None:
            continue
            
        # Convert template to grayscale if it has alpha channel
        if template.shape[2] == 4:
            # Use alpha channel as mask
            template_rgb = template[:,:,:3]
            template_mask = template[:,:,3]
            template_gray = cv2.cvtColor(template_rgb, cv2.COLOR_BGR2GRAY)
            
            # Convert ROI to grayscale
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Resize template if needed
            if template_gray.shape[0] > roi_gray.shape[0] or template_gray.shape[1] > roi_gray.shape[1]:
                scale = min(roi_gray.shape[0] / template_gray.shape[0], 
                           roi_gray.shape[1] / template_gray.shape[1])
                new_size = (int(template_gray.shape[1] * scale), int(template_gray.shape[0] * scale))
                template_gray = cv2.resize(template_gray, new_size)
                template_mask = cv2.resize(template_mask, new_size)
            
            # Template matching
            result = cv2.matchTemplate(roi_gray, template_gray, cv2.TM_CCOEFF_NORMED, mask=template_mask)
        else:
            # Convert to grayscale
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Resize template if needed
            if template_gray.shape[0] > roi_gray.shape[0] or template_gray.shape[1] > roi_gray.shape[1]:
                scale = min(roi_gray.shape[0] / template_gray.shape[0], 
                           roi_gray.shape[1] / template_gray.shape[1])
                new_size = (int(template_gray.shape[1] * scale), int(template_gray.shape[0] * scale))
                template_gray = cv2.resize(template_gray, new_size)
            
            # Template matching
            result = cv2.matchTemplate(roi_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Get best match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > best_score:
            best_score = max_val
            best_match = cursor_type
    
    # Add threshold for more confidence
    threshold = 0.6
    if best_score < threshold:
        return "NONE"
        
    return best_match
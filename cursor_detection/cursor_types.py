"""Cursor type detection functions"""
import cv2
import numpy as np


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
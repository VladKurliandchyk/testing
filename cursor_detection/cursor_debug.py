"""Debug utilities for cursor detection"""
import cv2
import time
import os
import numpy as np
from .cursor_detection import detect_cursor_state, DEBUG, DEBUG_FOLDER


def debug_save_roi(roi, prefix="roi"):
    """Save ROI debug image if debugging is enabled"""
    if not DEBUG:
        return
        
    timestamp = int(time.time() * 1000)
    cv2.imwrite(f"{DEBUG_FOLDER}/{prefix}_{timestamp}.png", roi)


def debug_save_masks(roi, hsv):
    """Save all detection masks for debugging"""
    if not DEBUG:
        return
        
    timestamp = int(time.time() * 1000)
    
    # Save different masks
    # Red masks for prohibited sign
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Sword masks
    lower_sword_red1 = np.array([0, 140, 160])
    upper_sword_red1 = np.array([10, 255, 255])
    lower_sword_red2 = np.array([170, 140, 160])
    upper_sword_red2 = np.array([180, 255, 255])
    
    mask_sword1 = cv2.inRange(hsv, lower_sword_red1, upper_sword_red1)
    mask_sword2 = cv2.inRange(hsv, lower_sword_red2, upper_sword_red2)
    mask_sword = cv2.bitwise_or(mask_sword1, mask_sword2)
    
    # Hand masks
    lower_hand1 = np.array([10, 30, 80])
    upper_hand1 = np.array([25, 140, 220])
    lower_hand2 = np.array([20, 25, 100])
    upper_hand2 = np.array([30, 130, 230])
    
    mask_hand1 = cv2.inRange(hsv, lower_hand1, upper_hand1)
    mask_hand2 = cv2.inRange(hsv, lower_hand2, upper_hand2)
    mask_hand = cv2.bitwise_or(mask_hand1, mask_hand2)
    
    # Save all masks
    cv2.imwrite(f"{DEBUG_FOLDER}/mask_red_{timestamp}.png", mask_red)
    cv2.imwrite(f"{DEBUG_FOLDER}/mask_sword_{timestamp}.png", mask_sword)
    cv2.imwrite(f"{DEBUG_FOLDER}/mask_hand_{timestamp}.png", mask_hand)
    
    # Save pixel counts
    with open(f"{DEBUG_FOLDER}/pixel_counts_{timestamp}.txt", "w") as f:
        f.write(f"Sword pixels: {cv2.countNonZero(mask_sword)}\n")
        f.write(f"Hand pixels: {cv2.countNonZero(mask_hand)}\n")
        f.write(f"Red pixels: {cv2.countNonZero(mask_red)}\n")


def debug_save_cursor_sample(frame, target_x, target_y, detected_state):
    """Save a debug sample with the detected cursor state overlaid"""
    if not DEBUG:
        return
        
    timestamp = int(time.time() * 1000)
    sample_radius = 50
    
    # Clone frame and draw debug info
    debug_frame = frame.copy()
    
    # Draw target crosshair
    cv2.line(debug_frame, (target_x - 10, target_y), (target_x + 10, target_y), (0, 255, 0), 2)
    cv2.line(debug_frame, (target_x, target_y - 10), (target_x, target_y + 10), (0, 255, 0), 2)
    
    # Draw search area
    cv2.rectangle(debug_frame, 
                 (target_x - sample_radius, target_y - sample_radius),
                 (target_x + sample_radius, target_y + sample_radius),
                 (255, 255, 0), 2)
    
    # Add text with detected state
    cv2.putText(debug_frame, f"State: {detected_state}", 
               (target_x - sample_radius, target_y - sample_radius - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    
    cv2.imwrite(f"{DEBUG_FOLDER}/debug_sample_{detected_state}_{timestamp}.png", debug_frame)


def analyze_cursor_regions(frame):
    """
    Helper function to analyze cursor detection across the entire frame.
    Returns a visualization of detected cursor states.
    """
    if not DEBUG:
        return None
        
    height, width = frame.shape[:2]
    vis_img = frame.copy()
    
    # Sample regions across the frame
    step = 50
    for y in range(step, height, step):
        for x in range(step, width, step):
            state = detect_cursor_state(frame, x, y, search_radius=20)
            
            # Draw different colors for different states
            if state == "RED_SWORD":
                color = (0, 0, 255)  # Red
            elif state == "HAND":
                color = (0, 255, 255)  # Yellow
            elif state == "PROHIBITED":
                color = (255, 0, 0)  # Blue
            else:
                continue  # Skip NONE
                
            cv2.circle(vis_img, (x, y), 5, color, -1)
            cv2.putText(vis_img, state[:1], (x-5, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    return vis_img
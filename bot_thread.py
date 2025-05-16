"""Main bot logic thread"""
import threading
import time
import cv2
import numpy as np
import win32gui
from PIL import Image
from mss import mss
from collections import Counter
import os
import sys

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from input_controller import (
    smooth_move as input_smooth_move, 
    click_mouse, 
    press_mouse, 
    release_mouse, 
    move_mouse_rel,
    press_key,
    release_key
)
from utils import (
    detect_obstacle_direction, 
    DEBUG, 
    DEAD_TIMEOUT, 
    CLICK_INTERVAL,
    POST_CLICK_DELAY,
    CURSOR_UPDATE_INTERVAL,
    class_names
)
# Import the cursor detection modules from the cursor_detection package
from cursor_detection.cursor_detection import detect_cursor_state, load_templates
from detection.yolo_detector import YOLODetector


class BotThread(threading.Thread):
    def __init__(self, window, detector):
        super().__init__(daemon=True)
        self.window = window
        self.detector = detector
        self.running = False
        self.current_target = None
        self.attacking = False
        self.last_click_time = 0
        self.dead_zones = []
        self.prohibited_zones = []
        self.sct = None
        self.bbox = None
        self.last_attack_time = 0
        self.attack_count = 0
        self.target_cursor_state = None
        self.target_tracking_active = False
        self.cursor_tracking_thread = None
        
        # Load cursor templates at initialization
        # Make sure to use the correct path to templates
        load_templates()
        
    def is_in_dead_zone(self, cx, cy):
        now = time.time()
        # Clean up expired dead zones
        self.dead_zones = [(x, y, t) for (x, y, t) in self.dead_zones if now - t < DEAD_TIMEOUT]
        # Clean up expired prohibited zones - using 9 seconds for these
        self.prohibited_zones = [(x, y, t) for (x, y, t) in self.prohibited_zones if now - t < 9.0]
        
        # Check both lists
        for dx, dy, _ in self.dead_zones:
            if abs(cx - dx) < 50 and abs(cy - dy) < 30:
                return True
                
        for px, py, _ in self.prohibited_zones:
            if abs(cx - px) < 50 and abs(cy - py) < 30:
                return True
                
        return False

    def smooth_move(self, tx, ty, steps=5, delay=0.002):
        """Wrapper for input controller smooth move"""
        input_smooth_move(tx, ty, steps, delay)

    def cursor_tracking_loop(self):
        """Thread function for continuously keeping cursor on target"""
        target_x, target_y = None, None
        try:
            while self.target_tracking_active and self.current_target:
                if not self.running:
                    break
                
                # Get fresh target coordinates
                if self.current_target:
                    target_x = int(self.current_target.cx + self.bbox['left'])
                    target_y = int(self.current_target.cy + self.bbox['top'])
                    
                    # Move cursor smoothly to updated target position
                    self.smooth_move(target_x, target_y, steps=3, delay=0.001)
                
                time.sleep(CURSOR_UPDATE_INTERVAL)
                
        except Exception as e:
            if DEBUG:
                print(f"Error in cursor tracking thread: {e}")

    def start_cursor_tracking(self):
        """Start continuous cursor tracking on a separate thread"""
        self.target_tracking_active = True
        if self.cursor_tracking_thread is None or not self.cursor_tracking_thread.is_alive():
            self.cursor_tracking_thread = threading.Thread(
                target=self.cursor_tracking_loop, 
                daemon=True
            )
            self.cursor_tracking_thread.start()
            if DEBUG:
                print("Started cursor tracking thread")

    def stop_cursor_tracking(self):
        """Stop the cursor tracking thread"""
        self.target_tracking_active = False
        if self.cursor_tracking_thread and self.cursor_tracking_thread.is_alive():
            if DEBUG:
                print("Stopping cursor tracking thread")

    def get_current_cursor_state(self, cx, cy):
        """Get the current cursor state at target position"""
        img = self.sct.grab(self.bbox)
        frame = np.array(Image.frombytes('RGB', (img.width, img.height), img.rgb))
        # Switch RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # Detect cursor state at target position
        return detect_cursor_state(frame, cx, cy)

    def attack_target(self):
        """Attack current target with click and check cursor state"""
        if not self.current_target:
            return False
        
        # Ensure target coordinates are valid and within window
        cx = self.current_target.cx
        cy = self.current_target.cy
        
        # Get window dimensions from bbox
        window_width = self.bbox['width']
        window_height = self.bbox['height']
        
        # Check if coordinates are valid
        if cx < 0 or cx >= window_width or cy < 0 or cy >= window_height:
            if DEBUG: print(f"Invalid target coordinates: ({cx}, {cy}) outside window {window_width}x{window_height}")
            return False
        
        tx = int(cx + self.bbox['left'])
        ty = int(cy + self.bbox['top'])
        
        # Make sure we're actively tracking the cursor on the target
        if not self.target_tracking_active:
            self.start_cursor_tracking()
        
        # Move to target and stay there - done by tracking thread
        # Just make sure we're there before checking cursor state
        self.smooth_move(tx, ty)
        
        # Check cursor state before clicking
        cursor_samples = []
        for _ in range(3):  # Take 3 samples
            cursor_state = self.get_current_cursor_state(cx, cy)
            cursor_samples.append(cursor_state)
            time.sleep(0.02)  # Short delay between samples
        
        # Use most common cursor state from samples
        self.target_cursor_state = Counter(cursor_samples).most_common(1)[0][0]
        
        if DEBUG: print(f"Cursor state at ({cx}, {cy}): {self.target_cursor_state} (samples: {cursor_samples})")
        
        # Handle different cursor states
        if self.target_cursor_state == "PROHIBITED":
            # Target is dead or prohibited - add to prohibited zones
            if DEBUG and self.current_target:
                print(f"Target {self.current_target.class_name} has prohibition symbol - adding to prohibited zones")
            self.prohibited_zones.append((cx, cy, time.time()))
            self.stop_cursor_tracking()
            return False
            
        elif self.target_cursor_state == "HAND":
            # Target is dead but has loot - click to pick up item
            click_mouse('left')
            time.sleep(0.2)
            if DEBUG and self.current_target:
                print(f"Target {self.current_target.class_name} shows hand cursor - looting")
            self.dead_zones.append((cx, cy, time.time()))
            self.stop_cursor_tracking()
            return False
        
        elif self.target_cursor_state == "RED_SWORD":
            # Target is alive and attackable - continue attacking
            click_mouse('left')
            self.last_attack_time = time.time()
            self.attack_count += 1
            time.sleep(0.1)
            return True
        
        else:  # "NONE" or any other state
            # Try clicking and check if cursor state changes
            click_mouse('left')
            self.last_attack_time = time.time()
            self.attack_count += 1
            time.sleep(0.1)
            
            # Check cursor state again after attack
            new_cursor_state = self.get_current_cursor_state(cx, cy)
            if DEBUG: print(f"Cursor state after attack: {new_cursor_state}")
            
            if new_cursor_state == "RED_SWORD":
                # Target is alive - continue attacking
                return True
            elif new_cursor_state == "HAND":
                # Target died and has loot
                click_mouse('left')  # Pick up the loot
                time.sleep(0.2)
                self.dead_zones.append((cx, cy, time.time()))
                self.stop_cursor_tracking()
                return False
            elif new_cursor_state == "PROHIBITED":
                # Target died or is prohibited
                self.prohibited_zones.append((cx, cy, time.time()))
                self.stop_cursor_tracking()
                return False
            else:
                # Can't determine state, assume target is still alive
                return True

    def smooth_rotate_camera(self, total_dx=200, steps=5, delay=0.03):
        press_mouse('right')
        step_dx = total_dx // steps
        for _ in range(steps):
            move_mouse_rel(step_dx, 0)
            time.sleep(delay)
        release_mouse('right')

    def run(self):
        hwnd = getattr(self.window, '_hWnd', None)
        if hwnd:
            win32gui.ShowWindow(hwnd, 5)
            win32gui.SetForegroundWindow(hwnd)
        
        self.bbox = {
            'left': self.window.left,
            'top': self.window.top,
            'width': self.window.width,
            'height': self.window.height
        }
        
        # Ensure cursor templates are loaded at startup
        load_templates()
        
        with mss() as sct:
            self.sct = sct
            self.running = True
            
            while self.running:
                # Get current frame
                img = sct.grab(self.bbox)
                frame = np.array(Image.frombytes('RGB', (img.width, img.height), img.rgb))
                dets = self.detector.detect(frame)

                # If we have a current target, attack it
                if self.attacking and self.current_target:
                    time_since_attack = time.time() - self.last_attack_time
                    
                    if time_since_attack < POST_CLICK_DELAY:
                        time.sleep(0.05)
                        continue
                    
                    # Check if target still exists in detections
                    same_class = [d for d in dets if d.class_name == self.current_target.class_name]
                    
                    if same_class:
                        # Update to closest detection of same class
                        closest_target = min(
                            same_class,
                            key=lambda d: (d.cx - self.current_target.cx) ** 2 + (d.cy - self.current_target.cy) ** 2
                        )
                        
                        # If target moved too far, allow cursor tracking to be updated
                        old_x, old_y = self.current_target.cx, self.current_target.cy
                        new_x, new_y = closest_target.cx, closest_target.cy
                        dist_sq = (new_x - old_x) ** 2 + (new_y - old_y) ** 2
                        
                        if dist_sq > 25:  # 5px distance threshold squared  
                            self.current_target = closest_target
                            if DEBUG:
                                print(f"Target moved: ({old_x},{old_y}) -> ({new_x},{new_y})")
                        
                        # Attack and check if still alive
                        target_alive = self.attack_target()
                        if not target_alive:
                            self.current_target = None
                            self.attack_count = 0
                            self.target_cursor_state = None
                            self.stop_cursor_tracking()
                        else:
                            time.sleep(CLICK_INTERVAL)
                            continue
                    else:
                        # Target no longer visible
                        if time_since_attack < POST_CLICK_DELAY * 3:
                            time.sleep(0.1)
                            continue
                            
                        self.current_target = None
                        self.attack_count = 0
                        self.target_cursor_state = None
                        self.stop_cursor_tracking()
                
                # Find new target if we don't have one (but might still be in attacking state)
                if self.attacking and self.current_target is None:
                    targets = [d for d in dets if d.class_name in class_names and not self.is_in_dead_zone(d.cx, d.cy)]
                    if targets:
                        self.current_target = targets[0]
                        self.attack_count = 0
                        self.last_attack_time = time.time() - POST_CLICK_DELAY
                        if DEBUG: print(f"New target: {self.current_target.class_name}")
                        self.start_cursor_tracking()
                        continue
                    else:
                        time.sleep(0.05)
                
                # Handle case when not attacking or need to start attacking
                elif not self.attacking:
                    targets = [d for d in dets if d.class_name in class_names and not self.is_in_dead_zone(d.cx, d.cy)]
                    if targets:
                        self.current_target = targets[0]
                        self.attacking = True
                        self.attack_count = 0
                        self.last_attack_time = time.time() - POST_CLICK_DELAY
                        if DEBUG: print(f"New target: {self.current_target.class_name}")
                        self.start_cursor_tracking()
                        continue
                
                    # No targets, rotate camera and move
                    self.smooth_rotate_camera()
                    time.sleep(0.1)
                    
                    # Check for obstacles and move
                    dir = detect_obstacle_direction(frame)
                    if dir == 'left':
                        press_mouse('right')
                        move_mouse_rel(-200, 0)
                        release_mouse('right')
                    elif dir == 'right':
                        press_mouse('right')
                        move_mouse_rel(200, 0)
                        release_mouse('right')
                    else:
                        press_key(ord('W'))
                        time.sleep(0.2)
                        release_key(ord('W'))
                    
                    time.sleep(0.05)

    def stop(self):
        self.running = False
        self.attacking = False
        self.current_target = None
        self.stop_cursor_tracking()
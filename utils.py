"""Configuration and utility functions"""
import yaml
import os
import cv2
import numpy as np
import pygetwindow as gw

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load configuration
with open(os.path.join(SCRIPT_DIR, 'config.yaml'), 'r') as f:
    CFG = yaml.safe_load(f)

# Configuration constants
OBSTACLE_THRESHOLD = CFG['obstacle_threshold']
DEBUG = CFG.get('debug', False)
DEAD_TIMEOUT = CFG.get('dead_timeout', 5.0)
CAMERA_ROTATE_TIME = CFG.get('camera_rotate_time', 0.3)
CLICK_INTERVAL = CFG.get('click_interval', 0.4)
POST_CLICK_DELAY = CFG.get('post_click_delay', 1.1)
CURSOR_UPDATE_INTERVAL = CFG.get('cursor_update_interval', 0.05)

# Model configuration
weights_path = os.path.join(SCRIPT_DIR, 'data', 'models', CFG['model_filename'])
class_names = CFG['classes']


def detect_obstacle_direction(frame):
    """Detect obstacle direction from bottom of frame"""
    h, w = frame.shape[:2]
    if h < 10: 
        return None
    
    seg = frame[h-10:h]
    third = w // 3
    left = seg[:, :third].mean()
    mid = seg[:, third:2*third].mean()
    right = seg[:, 2*third:].mean()
    
    if mid < OBSTACLE_THRESHOLD:
        return 'left' if left > right else 'right'
    return None


def choose_window():
    """Allow user to choose a window from all available windows"""
    titles = [w for w in gw.getAllTitles() if w.strip()]
    print("\nВыберите окно:")
    for i, t in enumerate(titles): 
        print(f"{i+1}: {t}")
    
    while True:
        try:
            idx = int(input("Введите номер: ")) - 1
            return gw.getWindowsWithTitle(titles[idx])[0]
        except:
            print("Неверный ввод, попробуйте снова.")
"""Input handling and mouse/keyboard control utilities"""
import ctypes
from ctypes import wintypes
import time

# Windows constants
PUL = ctypes.POINTER(ctypes.c_ulong)
KEYEVENTF_KEYUP      = 0x0002
KEYEVENTF_SCANCODE   = 0x0008
INPUT_KEYBOARD       = 1
INPUT_MOUSE          = 0
MOUSEEVENTF_MOVE     = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_RIGHTDOWN= 0x0008
MOUSEEVENTF_RIGHTUP  = 0x0010
VK_RIGHT_ARROW       = 0x27

screen_width  = ctypes.windll.user32.GetSystemMetrics(0)
screen_height = ctypes.windll.user32.GetSystemMetrics(1)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]


def press_key(vk):
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    inp = Input(INPUT_KEYBOARD, Input_I(ki=KeyBdInput(0, scan, KEYEVENTF_SCANCODE, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def release_key(vk):
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    inp = Input(INPUT_KEYBOARD, Input_I(ki=KeyBdInput(0, scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def press_mouse(btn):
    code = MOUSEEVENTF_LEFTDOWN if btn == 'left' else MOUSEEVENTF_RIGHTDOWN
    inp = Input(INPUT_MOUSE, Input_I(mi=MouseInput(0, 0, 0, code, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def release_mouse(btn):
    code = MOUSEEVENTF_LEFTUP if btn == 'left' else MOUSEEVENTF_RIGHTUP
    inp = Input(INPUT_MOUSE, Input_I(mi=MouseInput(0, 0, 0, code, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def move_mouse(x, y):
    x = max(0, min(x, screen_width - 1))
    y = max(0, min(y, screen_height - 1))
    ax = int(x * 65535 / (screen_width - 1))
    ay = int(y * 65535 / (screen_height - 1))
    inp = Input(INPUT_MOUSE, Input_I(mi=MouseInput(ax, ay, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def move_mouse_rel(dx, dy):
    inp = Input(INPUT_MOUSE, Input_I(mi=MouseInput(dx, dy, 0, MOUSEEVENTF_MOVE, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def click_mouse(button):
    press_mouse(button)
    time.sleep(0.02)
    release_mouse(button)


def smooth_move(tx, ty, steps=5, delay=0.002):
    """Smoothly move cursor from current position to target position"""
    pt = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    dx = (tx - pt.x) / steps
    dy = (ty - pt.y) / steps
    for i in range(steps):
        move_mouse(int(pt.x + dx * (i + 1)), int(pt.y + dy * (i + 1)))
        time.sleep(delay)
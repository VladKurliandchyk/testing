"""Main GUI application"""
import tkinter as tk
from pynput import keyboard

from bot_thread import BotThread
from utils import choose_window, weights_path, class_names
from detection.yolo_detector import YOLODetector


class GameBotApp:
    def __init__(self, root, window):
        self.window = window
        self.root = root
        self.bot = None
        
        # Initialize detector
        self.detector = YOLODetector(weights_path, class_names)
        
        # Setup GUI
        root.geometry('300x200')
        root.configure(bg='#1e1e1e')
        root.title('Game Bot')
        
        tk.Label(root, text='🎮 Game Bot', bg='#1e1e1e', fg='white', 
                font=('Arial',14,'bold')).pack(pady=10)
                
        tk.Button(root, text='▶ Start', width=20, command=self.start, 
                 bg='#28a745', fg='white').pack(pady=5)
                 
        tk.Button(root, text='⏹ Stop', width=20, command=self.stop, 
                 bg='#dc3545', fg='white').pack(pady=5)
                 
        self.status = tk.Label(root, text='⏳ Idle', bg='#1e1e1e', fg='gray')
        self.status.pack(pady=10)
        
        # Start keyboard listener for hotkeys
        keyboard.Listener(on_press=self.handle_hotkey).start()

    def start(self):
        """Start the bot thread"""
        if not self.bot or not self.bot.is_alive():
            self.bot = BotThread(self.window, self.detector)
            self.bot.start()
        self.status.config(text='🟢 Running', fg='lightgreen')

    def stop(self):
        """Stop the bot thread"""
        if self.bot:
            self.bot.stop()
        self.status.config(text='🔴 Stopped', fg='red')

    def handle_hotkey(self, key):
        """Handle keyboard hotkeys (Home=start, End=stop)"""
        try:
            if key == keyboard.Key.home:
                self.start()
            elif key == keyboard.Key.end:
                self.stop()
        except Exception as e:
            print(f"Hotkey error: {e}")


if __name__ == '__main__':
    # Choose window and start application
    window = choose_window()
    root = tk.Tk()
    app = GameBotApp(root, window)
    root.mainloop()
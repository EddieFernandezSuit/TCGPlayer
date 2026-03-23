import pyautogui
from pynput import mouse

def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.right:
        current_pos = pyautogui.position()
        print(current_pos)
        if current_pos == (0, 0):
            return False

with mouse.Listener(on_click=on_click) as listener:
    listener.join()

    

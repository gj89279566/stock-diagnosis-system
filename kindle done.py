import os
import subprocess
import time
import pyautogui
from PIL import Image
import pytesseract

# 设置 Tesseract 可执行文件的路径（更新为你的安装路径）
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# Kindle 窗口名称
KINDLE_WINDOW = "Kindle"

# 截图保存目录（存到桌面）
SCREENSHOT_FOLDER = os.path.expanduser("~/Desktop/Kindle_Screenshots")
if not os.path.exists(SCREENSHOT_FOLDER):
    os.makedirs(SCREENSHOT_FOLDER)

# 全局变量：记录上一张截图 OCR 提取的文字和截图计数器
previous_text = None
screenshot_counter = 1

def activate_window(window_title):
    """激活指定窗口"""
    script = f'''
    tell application "System Events"
        set appList to name of every process
        if "{window_title}" is in appList then
            tell process "{window_title}" to perform action "AXRaise" of window 1
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    print(f"✅ 窗口 {window_title} 已激活")

def maximize_window_applescript(window_title):
    """用 AppleScript 让窗口进入全屏"""
    script = f'''
    tell application "System Events"
        tell process "{window_title}"
            set frontmost to true
            try
                keystroke "f" using {{command down, control down}}
            on error
                display notification "⚠️ 该应用可能不支持全屏" with title "窗口最大化失败"
            end try
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    print("🖥️  窗口已进入全屏模式")

def capture_screenshot():
    """截图、使用 OCR 提取文字对比，并按顺序命名保存缩小后的图片"""
    global previous_text, screenshot_counter

    time.sleep(2)  # 确保 Kindle 页面加载完成
    screenshot = pyautogui.screenshot()
    
    # 使用 OCR 提取截图中的文字（转换为灰度图可以提高识别率）
    ocr_text = pytesseract.image_to_string(screenshot.convert("L"))
    ocr_text = ocr_text.strip()

    # 缩小图片尺寸（例如缩小到原来的 50%）
    new_width = int(screenshot.width * 0.5)
    new_height = int(screenshot.height * 0.5)
    screenshot_resized = screenshot.resize((new_width, new_height), Image.LANCZOS)

    # 按顺序命名图片，例如 001.png, 002.png, ...
    screenshot_filename = f"{screenshot_counter:03d}.png"
    screenshot_path = os.path.join(SCREENSHOT_FOLDER, screenshot_filename)
    screenshot_resized.save(screenshot_path, optimize=True)
    print(f"📸 截图已保存: {screenshot_path}")
    screenshot_counter += 1

    # 对比当前 OCR 提取的文字与上一张的 OCR 文字
    if previous_text is not None:
        if ocr_text == previous_text:
            print("⚠️ 检测到重复页面（基于 OCR 文字），询问是否退出...")
            user_choice = pyautogui.confirm("检测到重复页面，是否退出程序？", buttons=["继续", "退出"])
            if user_choice == "退出":
                print("🛑 退出程序")
                exit(0)
    previous_text = ocr_text

def turn_page():
    """模拟 Kindle 翻页：点击屏幕右侧区域"""
    time.sleep(1)
    screenWidth, screenHeight = pyautogui.size()
    # 点击右侧区域中间位置（可根据实际情况调整比例）
    clickX = int(screenWidth * 0.9)
    clickY = int(screenHeight / 2)
    pyautogui.click(clickX, clickY)
    print(f"📖 已点击屏幕位置 ({clickX}, {clickY}) 翻页")

def main():
    activate_window(KINDLE_WINDOW)   # 激活 Kindle 窗口
    time.sleep(2)
    maximize_window_applescript(KINDLE_WINDOW)  # 进入全屏
    time.sleep(3)
    while True:
        capture_screenshot()  # 截图并比较 OCR 文字
        turn_page()           # 翻页
        time.sleep(3)

if __name__ == "__main__":
    main()
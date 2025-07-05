import subprocess
import pyautogui
import pytesseract
import os
from PIL import Image
import time

# 设置 Tesseract OCR 路径（如果需要手动指定路径）
# macOS (Homebrew 安装)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
# Windows（如果未自动识别）
# pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def activate_window(window_title):
    """激活 Kindle 窗口（适用于 macOS）"""
    script = f'''
    tell application "System Events"
        set appList to name of every process
        if "{window_title}" is in appList then
            tell process "{window_title}" to perform action "AXRaise" of window 1
            set frontmost of application "{window_title}" to true
        end if
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        print(f"✅ 窗口 {window_title} 已激活")
    except subprocess.CalledProcessError as e:
        print(f"❌ 激活窗口失败: {e}")

# 激活 Kindle 窗口
activate_window("Kindle")
time.sleep(2)  # 等待窗口切换完成

# 获取桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# 在桌面创建 `progress_screenshots` 目录
OUTPUT_FOLDER = os.path.join(desktop_path, "progress_screenshots")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 进度条截图区域 (x, y, width, height) - 适当加大区域
PROGRESS_REGION = (1210, 760, 60, 30)  # 扩大区域，确保完整覆盖进度条

# 截取进度条区域
screenshot_path = os.path.join(OUTPUT_FOLDER, "progress_debug.png")
screenshot = pyautogui.screenshot(region=PROGRESS_REGION)
screenshot.save(screenshot_path)

print(f"📸 进度条截图已保存到 {screenshot_path}")

# 使用 OCR 识别进度条中的百分比数字
img = Image.open(screenshot_path)

# OCR 识别进度条文本（仅识别数字）
progress_text = pytesseract.image_to_string(
    img, config="--psm 7 -c tessedit_char_whitelist=0123456789"
).strip()

# 输出识别结果
if progress_text.isdigit():
    print(f"📊 识别出的进度：{progress_text}%")
else:
    print("❌ 无法识别进度，请检查截图！")
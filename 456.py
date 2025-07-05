import pyautogui

def get_mouse_position():
    """ 鼠标点击后获取坐标 """
    print("请把鼠标移动到截图区域的左上角，然后点击")
    x1, y1 = pyautogui.position()  # 记录左上角
    print(f"左上角坐标：({x1}, {y1})")

    input("请把鼠标移动到截图区域的右下角，然后按回车")
    x2, y2 = pyautogui.position()  # 记录右下角
    print(f"右下角坐标：({x2}, {y2})")

    width = x2 - x1
    height = y2 - y1

    print(f"你的 SCREENSHOT_REGION 设为: ({x1}, {y1}, {width}, {height})")

if __name__ == "__main__":
    input("请把鼠标移动到截图区域的左上角，然后按回车...")
    get_mouse_position()
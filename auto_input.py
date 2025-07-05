import pyautogui
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import numpy as np
import pytesseract
import pandas as pd
from PIL import ImageGrab, Image, ImageDraw
import os

# 设置安全延迟
pyautogui.PAUSE = 1.0  # 每个操作之间暂停1秒
pyautogui.FAILSAFE = True  # 将鼠标移动到屏幕左上角可以终止程序

def capture_screen():
    """捕获屏幕截图"""
    screenshot = ImageGrab.grab()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def find_template(template_path, threshold=0.8):
    """在屏幕上查找模板图像"""
    print(f"正在查找模板: {template_path}")
    screen = capture_screen()
    template = cv2.imread(template_path)
    if template is None:
        raise ValueError(f"无法加载模板图像: {template_path}")
    
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"模板匹配度: {max_val:.2f}")
    if max_val >= threshold:
        print(f"找到匹配位置: {max_loc}")
        return max_loc
    print("未找到匹配")
    return None

def get_text_from_region(x, y, w, h):
    """从指定区域提取文本"""
    print(f"正在从区域 ({x}, {y}, {w}, {h}) 提取文本")
    screen = capture_screen()
    region = screen[y:y+h, x:x+w]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang='chi_sim+eng')
    print(f"提取到的文本: {text.strip()}")
    return text.strip()

def mark_click_position(x, y, duration=1):
    """在屏幕上标记点击位置"""
    # 获取屏幕截图
    screenshot = ImageGrab.grab()
    draw = ImageDraw.Draw(screenshot)
    
    # 绘制红色圆圈
    radius = 20
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline='red', width=3)
    
    # 保存标记后的图片
    temp_path = "click_position.png"
    screenshot.save(temp_path)
    
    # 显示图片
    img = cv2.imread(temp_path)
    cv2.imshow("Click Position", img)
    cv2.waitKey(int(duration * 1000))
    cv2.destroyAllWindows()
    
    # 删除临时文件
    os.remove(temp_path)

def show_mouse_position():
    """显示当前鼠标位置"""
    x, y = pyautogui.position()
    print(f"当前鼠标位置: x={x}, y={y}")
    return x, y

def activate_and_input(x, y, value):
    """激活单元格并输入数据"""
    # 移动鼠标到目标位置
    print(f"移动鼠标到位置: ({x}, {y})")
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.5)
    
    # 点击选中单元格
    print("点击选中单元格")
    pyautogui.click()
    time.sleep(0.5)
    
    # 尝试 Command+A 全选
    print("尝试全选")
    pyautogui.hotkey('command', 'a')
    time.sleep(0.5)
    
    # 输入新数据
    print(f"输入数据: {value}")
    pyautogui.write(str(value))
    time.sleep(0.5)
    
    # 按回车确认
    print("按回车确认")
    pyautogui.press('enter')
    time.sleep(0.5)

def main():
    # 创建GUI界面
    root = tk.Tk()
    root.title("智能自动输入工具")
    root.geometry("500x600")

    # 创建模板管理区域
    template_frame = tk.LabelFrame(root, text="模板管理", padx=5, pady=5)
    template_frame.pack(fill="x", padx=5, pady=5)

    templates = []
    template_vars = []

    def add_template():
        file_path = filedialog.askopenfilename(
            title="选择模板图像",
            filetypes=[("图像文件", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            templates.append(file_path)
            var = tk.StringVar(value=file_path)
            template_vars.append(var)
            update_template_list()

    def update_template_list():
        for widget in template_frame.winfo_children():
            widget.destroy()
        
        for i, (template, var) in enumerate(zip(templates, template_vars)):
            frame = tk.Frame(template_frame)
            frame.pack(fill="x", pady=2)
            
            tk.Label(frame, text=f"模板 {i+1}:").pack(side="left")
            tk.Entry(frame, textvariable=var, width=40).pack(side="left", padx=5)
            tk.Button(frame, text="删除", command=lambda idx=i: remove_template(idx)).pack(side="right")

    def remove_template(index):
        templates.pop(index)
        template_vars.pop(index)
        update_template_list()

    tk.Button(template_frame, text="添加模板", command=add_template).pack(pady=5)

    # Excel文件选择
    excel_frame = tk.LabelFrame(root, text="Excel文件", padx=5, pady=5)
    excel_frame.pack(fill="x", padx=5, pady=5)

    excel_path = tk.StringVar()
    tk.Entry(excel_frame, textvariable=excel_path, width=50).pack(side="left", padx=5)
    tk.Button(excel_frame, text="浏览", command=lambda: excel_path.set(
        filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx *.xls")])
    )).pack(side="right")

    # 状态显示
    status_label = tk.Label(root, text="准备就绪")
    status_label.pack(pady=5)

    def start_automation():
        if not templates:
            messagebox.showerror("错误", "请至少添加一个模板")
            return
        
        if not excel_path.get():
            messagebox.showerror("错误", "请选择Excel文件")
            return

        try:
            # 读取Excel文件
            print(f"正在读取Excel文件: {excel_path.get()}")
            df = pd.read_excel(excel_path.get())
            print(f"Excel数据行数: {len(df)}")
            
            # 显示倒计时
            for i in range(5, 0, -1):
                status_label.config(text=f"将在 {i} 秒后开始...")
                root.update()
                time.sleep(1)

            status_label.config(text="开始处理...")
            
            # 对每个模板进行匹配
            for template_path in templates:
                print(f"\n开始处理模板: {template_path}")
                location = find_template(template_path)
                if location:
                    x, y = location
                    # 获取模板图像尺寸
                    template = cv2.imread(template_path)
                    h, w = template.shape[:2]
                    
                    # 提取文本
                    text = get_text_from_region(x, y, w, h)
                    status_label.config(text=f"找到匹配: {text}")
                    
                    # 显示点击位置
                    click_x = x + w//2
                    click_y = y + h//2
                    print(f"准备点击位置: ({click_x}, {click_y})")
                    
                    # 显示当前鼠标位置
                    current_x, current_y = show_mouse_position()
                    print(f"当前鼠标位置: ({current_x}, {current_y})")
                    
                    # 标记并显示点击位置
                    mark_click_position(click_x, click_y)
                    
                    print("开始输入数据...")
                    for index, value in enumerate(df.iloc[:, 0]):
                        print(f"处理第 {index + 1} 行数据: {value}")
                        activate_and_input(click_x, click_y, value)
                        # 移动到下一个单元格
                        pyautogui.press('down')
                        time.sleep(0.5)
                else:
                    print(f"未找到模板匹配: {template_path}")
            
            status_label.config(text="处理完成！")
            messagebox.showinfo("完成", "所有数据已输入完成！")
            
        except Exception as e:
            print(f"发生错误: {str(e)}")
            messagebox.showerror("错误", f"发生错误: {str(e)}")
            status_label.config(text="发生错误！")

    # 开始按钮
    tk.Button(root, text="开始自动输入", command=start_automation).pack(pady=10)

    # 使用说明
    instructions = """
使用说明：
1. 添加模板：
   - 点击"添加模板"按钮
   - 选择要识别的界面元素截图（如输入框、按钮等）
   - 可以添加多个模板

2. 选择Excel文件：
   - 点击"浏览"按钮
   - 选择包含要输入数据的Excel文件

3. 开始自动输入：
   - 确保目标软件已打开
   - 点击"开始自动输入"按钮
   - 程序会自动识别界面元素并输入数据

提示：
- 模板图像应该清晰，包含要识别的界面元素
- Excel文件的第一列将被用作输入数据
- 将鼠标移动到屏幕左上角可以终止程序
"""
    tk.Label(root, text=instructions, justify='left', wraplength=480).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main() 
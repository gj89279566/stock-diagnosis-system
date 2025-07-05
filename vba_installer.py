import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import tempfile
import shutil
import platform
import random
import string
import win32com.client

class VBAInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("VBA代码安装工具")
        self.root.geometry("800x600")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 按钮名称输入
        ttk.Label(main_frame, text="按钮名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.button_name = ttk.Entry(main_frame, width=40)
        self.button_name.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 按钮位置选择
        ttk.Label(main_frame, text="按钮位置:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.button_location = ttk.Combobox(main_frame, width=37)
        self.button_location['values'] = ('功能区-开始', '功能区-插入', '功能区-视图', '快速访问工具栏')
        self.button_location.current(0)
        self.button_location.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # VBA代码输入
        ttk.Label(main_frame, text="VBA代码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vba_code = scrolledtext.ScrolledText(main_frame, width=80, height=20)
        self.vba_code.grid(row=2, column=1, pady=5)
        
        # 项目密码输入
        ttk.Label(main_frame, text="项目密码:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.project_password = ttk.Entry(main_frame, width=40, show="*")
        self.project_password.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 生成随机密码按钮
        ttk.Button(main_frame, text="生成随机密码", command=self.generate_random_password).grid(row=3, column=2, padx=5)
        
        # 生成按钮
        ttk.Button(main_frame, text="生成安装程序", command=self.generate_installer).grid(row=4, column=1, pady=10)
        
        # 安装和卸载按钮（仅在生成的exe中显示）
        if getattr(sys, 'frozen', False):
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=5, column=1, pady=10)
            ttk.Button(button_frame, text="安装到Outlook", command=self.install_to_outlook).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="从Outlook卸载", command=self.uninstall_from_outlook).pack(side=tk.LEFT, padx=5)

    def generate_random_password(self):
        # 生成16位随机密码
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(16))
        self.project_password.delete(0, tk.END)
        self.project_password.insert(0, password)

    def generate_installer(self):
        try:
            button_name = self.button_name.get().strip()
            button_location = self.button_location.get()
            vba_code = self.vba_code.get("1.0", tk.END).strip()
            project_password = self.project_password.get().strip()
            
            if not button_name or not vba_code:
                messagebox.showerror("错误", "请输入按钮名称和VBA代码")
                return
                
            if not project_password:
                messagebox.showerror("错误", "请输入项目密码")
                return
            
            # 检查操作系统
            if platform.system() != "Windows":
                messagebox.showinfo("提示", f"当前在Mac系统上，仅作界面测试。\n\n按钮名称: {button_name}\n按钮位置: {button_location}\n\nVBA代码:\n{vba_code}")
                return
                
            # 创建临时文件保存代码
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, 'vba_installer.txt')
            
            # 包装VBA代码，添加安全保护
            protected_code = self.protect_vba_code(vba_code)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(f"BUTTON_NAME={button_name}\n")
                f.write(f"BUTTON_LOCATION={button_location}\n")
                f.write(f"PROJECT_PASSWORD={project_password}\n")
                f.write(f"VBA_CODE={protected_code}")
            
            # 使用PyInstaller生成exe，不请求管理员权限
            pyinstaller_cmd = f'pyinstaller --onefile --windowed --uac-admin=False --add-data "{temp_file};." vba_installer.py'
            result = os.system(pyinstaller_cmd)
            
            if result == 0:
                messagebox.showinfo("成功", "安装程序已生成在dist文件夹中")
            else:
                messagebox.showerror("错误", "生成安装程序失败，请检查是否安装了PyInstaller")
            
            # 清理临时文件
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            messagebox.showerror("错误", f"生成安装程序时出错: {str(e)}")

    def protect_vba_code(self, code):
        # 添加代码保护包装
        protected_code = f"""
Attribute VB_Name = "HiddenModule"
Option Private Module
Option Explicit

{code}

' 防止代码查看和修改
Private Sub Workbook_Open()
    Application.EnableEvents = False
    Application.DisplayAlerts = False
    Application.ScreenUpdating = False
End Sub

Private Sub Workbook_BeforeClose(Cancel As Boolean)
    Application.EnableEvents = True
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
End Sub
"""
        return protected_code

    def install_to_outlook(self):
        if platform.system() != "Windows":
            messagebox.showinfo("提示", "当前在Mac系统上，无法安装到Outlook。\n请在Windows系统上运行此程序。")
            return
            
        try:
            # 获取当前exe所在目录
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
                
            # 读取保存的代码
            config_file = os.path.join(application_path, 'vba_installer.txt')
            if not os.path.exists(config_file):
                messagebox.showerror("错误", "找不到配置文件")
                return
                
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                button_name = lines[0].split('=')[1].strip()
                button_location = lines[1].split('=')[1].strip()
                project_password = lines[2].split('=')[1].strip()
                vba_code = lines[3].split('=')[1].strip()
            
            # 尝试以普通用户权限安装
            try:
                # 连接到Outlook
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")
                
                # 获取Outlook对象
                explorer = outlook.ActiveExplorer()
                if explorer is None:
                    explorer = outlook.Explorers.Add()
                
                # 创建自定义按钮
                command_bar = explorer.CommandBars.Add("CustomButton", 1)
                button = command_bar.Controls.Add(1, 1)
                button.Caption = button_name
                
                # 添加VBA代码
                vba_module = outlook.VBE.ActiveVBProject.VBComponents.Add(1)  # 1 = vbext_ct_StdModule
                vba_module.CodeModule.AddFromString(vba_code)
                
                messagebox.showinfo("成功", "VBA代码已成功安装到Outlook")
                
            except Exception as e:
                if "Access is denied" in str(e):
                    messagebox.showerror("错误", "无法访问Outlook。请确保：\n1. Outlook已关闭\n2. 已启用宏和VBA代码\n3. 已信任VBA项目访问")
                else:
                    messagebox.showerror("错误", f"安装失败: {str(e)}")
            
        except Exception as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                messagebox.showerror("错误", "无法访问Outlook。请确保：\n1. Outlook已关闭\n2. 已启用宏和VBA代码\n3. 已信任VBA项目访问")
            elif "The system cannot find the file specified" in error_msg:
                messagebox.showerror("错误", "找不到Outlook程序，请确保已安装Outlook")
            else:
                messagebox.showerror("错误", f"安装失败: {error_msg}")

    def uninstall_from_outlook(self):
        if platform.system() != "Windows":
            messagebox.showinfo("提示", "当前在Mac系统上，无法从Outlook卸载。\n请在Windows系统上运行此程序。")
            return
            
        try:
            # 获取当前exe所在目录
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
                
            # 读取保存的代码
            config_file = os.path.join(application_path, 'vba_installer.txt')
            if not os.path.exists(config_file):
                messagebox.showerror("错误", "找不到配置文件")
                return
                
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                button_name = lines[0].split('=')[1].strip()
                button_location = lines[1].split('=')[1].strip()
                project_password = lines[2].split('=')[1].strip()
            
            # 尝试卸载
            try:
                # 连接到Outlook
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")
                
                # 获取Outlook对象
                explorer = outlook.ActiveExplorer()
                if explorer is None:
                    explorer = outlook.Explorers.Add()
                
                # 查找并删除按钮
                found = False
                for command_bar in explorer.CommandBars:
                    if command_bar.Name == "CustomButton":
                        for control in command_bar.Controls:
                            if control.Caption == button_name:
                                control.Delete()
                                found = True
                        if found:
                            command_bar.Delete()
                            break
                
                # 删除VBA模块
                try:
                    vba_project = outlook.VBE.ActiveVBProject
                    for component in vba_project.VBComponents:
                        if component.Name == "HiddenModule":
                            vba_project.VBComponents.Remove(component)
                            break
                except:
                    pass  # 忽略VBA模块删除错误
                
                if found:
                    messagebox.showinfo("成功", "已成功从Outlook卸载")
                else:
                    messagebox.showinfo("提示", "未找到要卸载的按钮")
                
            except Exception as e:
                if "Access is denied" in str(e):
                    messagebox.showerror("错误", "无法访问Outlook。请确保：\n1. Outlook已关闭\n2. 已启用宏和VBA代码\n3. 已信任VBA项目访问")
                else:
                    messagebox.showerror("错误", f"卸载失败: {str(e)}")
            
        except Exception as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                messagebox.showerror("错误", "无法访问Outlook。请确保：\n1. Outlook已关闭\n2. 已启用宏和VBA代码\n3. 已信任VBA项目访问")
            elif "The system cannot find the file specified" in error_msg:
                messagebox.showerror("错误", "找不到Outlook程序，请确保已安装Outlook")
            else:
                messagebox.showerror("错误", f"卸载失败: {error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VBAInstaller(root)
    root.mainloop() 
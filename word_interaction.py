from appscript import app, k, mactypes
import time
import tkinter as tk
from tkinter import messagebox

class WordInteraction:
    def __init__(self):
        self.word_app = None
        self.current_doc = None
        self.last_selection = None
        self.is_running = False

    def connect_to_word(self):
        """连接到Word应用程序"""
        try:
            self.word_app = app('Microsoft Word')
            return True
        except Exception as e:
            print(f"连接Word失败: {str(e)}")
            return False

    def get_active_document(self):
        """获取当前活动的Word文档"""
        try:
            if self.word_app:
                self.current_doc = self.word_app.active_document.get()
                return True
        except Exception as e:
            print(f"获取活动文档失败: {str(e)}")
            return False
        return False

    def get_selected_text(self):
        """获取当前选中的文字"""
        try:
            if self.current_doc:
                selection = self.current_doc.selection.get()
                if selection:
                    return selection.text.get()
        except Exception as e:
            print(f"获取选中文字失败: {str(e)}")
        return None

    def get_selection_style(self):
        """获取选中文字的样式信息"""
        try:
            if self.current_doc:
                selection = self.current_doc.selection.get()
                if selection:
                    font = selection.font.get()
                    return {
                        'name': font.name.get(),
                        'size': font.size.get(),
                        'bold': font.bold.get(),
                        'italic': font.italic.get(),
                        'underline': font.underline.get()
                    }
        except Exception as e:
            print(f"获取样式信息失败: {str(e)}")
        return None

    def start_monitoring(self, callback):
        """开始监控Word中的文字选择"""
        self.is_running = True
        while self.is_running:
            try:
                if not self.current_doc:
                    if not self.get_active_document():
                        time.sleep(1)
                        continue

                selected_text = self.get_selected_text()
                if selected_text != self.last_selection:
                    self.last_selection = selected_text
                    if selected_text:
                        style_info = self.get_selection_style()
                        if style_info:
                            callback(selected_text, style_info)

            except Exception as e:
                print(f"监控过程出错: {str(e)}")
                time.sleep(1)

            time.sleep(0.5)  # 降低CPU使用率

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False

class WordMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word样式监控器")
        
        # 创建Word交互对象
        self.word_interaction = WordInteraction()
        
        # 创建界面元素
        self.create_widgets()
        
        # 连接Word
        if not self.word_interaction.connect_to_word():
            messagebox.showerror("错误", "无法连接到Word应用程序")
            return

    def create_widgets(self):
        """创建界面元素"""
        # 状态标签
        self.status_label = tk.Label(self.root, text="等待连接Word...")
        self.status_label.pack(pady=5)

        # 选中文字显示
        self.text_frame = tk.LabelFrame(self.root, text="选中的文字")
        self.text_frame.pack(padx=10, pady=5, fill=tk.X)
        self.selected_text_label = tk.Label(self.text_frame, text="", wraplength=400)
        self.selected_text_label.pack(padx=5, pady=5)

        # 样式信息显示
        self.style_frame = tk.LabelFrame(self.root, text="样式信息")
        self.style_frame.pack(padx=10, pady=5, fill=tk.X)
        self.style_text = tk.Text(self.style_frame, height=6, wrap=tk.WORD)
        self.style_text.pack(padx=5, pady=5, fill=tk.X)

        # 控制按钮
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)
        
        self.start_button = tk.Button(self.button_frame, text="开始监控", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(self.button_frame, text="停止监控", command=self.stop_monitoring)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.config(state=tk.DISABLED)

    def update_display(self, text, style_info):
        """更新显示信息"""
        self.selected_text_label.config(text=text)
        
        # 更新样式信息
        style_text = f"字体: {style_info['name']}\n"
        style_text += f"大小: {style_info['size']}\n"
        style_text += f"加粗: {'是' if style_info['bold'] else '否'}\n"
        style_text += f"斜体: {'是' if style_info['italic'] else '否'}\n"
        style_text += f"下划线: {'是' if style_info['underline'] else '否'}"
        
        self.style_text.delete(1.0, tk.END)
        self.style_text.insert(tk.END, style_text)

    def start_monitoring(self):
        """开始监控"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="正在监控Word...")
        
        # 在新线程中启动监控
        import threading
        self.monitor_thread = threading.Thread(
            target=self.word_interaction.start_monitoring,
            args=(self.update_display,)
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.word_interaction.stop_monitoring()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="监控已停止")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordMonitorApp(root)
    root.mainloop() 
import tkinter as tk
from tkinter import filedialog, messagebox
from docx import Document

class WordStyleAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Word样式分析器")
        self.create_widgets()

    def create_widgets(self):
        # 选择文件按钮
        self.select_button = tk.Button(self.root, text="选择Word文件", command=self.open_file)
        self.select_button.pack(pady=10)

        # 样式信息显示区域
        self.style_display = tk.Text(self.root, height=25, width=90, wrap=tk.WORD)
        self.style_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Word 文件", "*.docx")])
        if not file_path:
            return
        try:
            doc = Document(file_path)
            self.analyze_and_display(doc)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取Word文件: {str(e)}")

    def analyze_and_display(self, doc):
        self.style_display.delete(1.0, tk.END)
        style_counter = {}  # key: (段落样式, 字体, 字号, 加粗, 斜体, 下划线), value: [字数, [示例列表]]
        for para in doc.paragraphs:
            para_style = para.style.name if para.style else '未知'
            for run in para.runs:
                text = run.text.strip()
                if not text:
                    continue
                font = run.font.name or (run.style.font.name if run.style and run.style.font and run.style.font.name else '默认')
                size = run.font.size.pt if run.font.size else (run.style.font.size.pt if run.style and run.style.font and run.style.font.size else '?')
                bold = bool(run.bold)
                italic = bool(run.italic)
                underline = bool(run.underline)
                key = (para_style, font, size, bold, italic, underline)
                if key not in style_counter:
                    style_counter[key] = [0, []]
                style_counter[key][0] += len(text)
                # 收集示例内容，累计不少于20字，内容之间用/分隔
                example_list = style_counter[key][1]
                total_len = sum(len(e) for e in example_list)
                if total_len < 20:
                    # 避免重复追加同一内容
                    if text not in example_list:
                        example_list.append(text)
        # 显示统计结果
        for (para_style, font, size, bold, italic, underline), (count, example_list) in sorted(style_counter.items(), key=lambda x: (-x[1][0], x[0][0])):
            # 拼接示例内容，直到累计不少于20字
            example = ''
            total = 0
            for idx, e in enumerate(example_list):
                if idx > 0:
                    example += '/'
                example += e
                total += len(e)
                if total >= 20:
                    break
            info = f"段落样式: {para_style}\n字体: {font}, 大小: {size}, 加粗: {'是' if bold else '否'}, 斜体: {'是' if italic else '否'}, 下划线: {'是' if underline else '否'}\n出现字数: {count}\n示例: {example}\n"
            self.style_display.insert(tk.END, info + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordStyleAnalyzer(root)
    root.mainloop()
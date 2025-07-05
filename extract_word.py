import tkinter as tk
from tkinter import filedialog
from docx import Document
import os
from docx.table import Table
from docx.text.paragraph import Paragraph
import re

def select_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Word files", "*.docx"), ("All files", "*.*")]
    )
    if file_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

def iter_block_items(parent):
    """
    依次遍历文档中的段落和表格，保持原始顺序
    """
    for child in parent.element.body.iterchildren():
        if child.tag.endswith('tbl'):
            yield Table(child, parent)
        elif child.tag.endswith('p'):
            yield Paragraph(child, parent)

def is_heading_style(style_name):
    # 支持中英文、带空格、数字的标题样式
    return bool(re.match(r'^(Heading|标题)\s*\d+$', style_name, re.IGNORECASE))

def extract_content():
    file_path = entry_path.get()
    if not file_path:
        return

    try:
        doc = Document(file_path)
        output_text = []

        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                style = block.style.name.strip()
                if is_heading_style(style):
                    output_text.append(block.text)
                elif block.text.strip():
                    output_text.append(block.text)
            elif isinstance(block, Table):
                output_text.append("\n[表格开始]")
                for row in block.rows:
                    row_text = []
                    for cell in row.cells:
                        cell_text = []
                        for para in cell.paragraphs:
                            if para.text.strip():
                                cell_text.append(para.text)
                        row_text.append('\n'.join(cell_text))
                    output_text.append(" | ".join(row_text))
                output_text.append("[表格结束]\n")

        output_file = os.path.splitext(file_path)[0] + "_extracted.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_text))

        status_label.config(text=f"内容已提取到: {output_file}")

    except Exception as e:
        status_label.config(text=f"错误: {str(e)}")

# 创建主窗口
root = tk.Tk()
root.title("Word文档内容提取工具")
root.geometry("600x400")

# 创建界面组件
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(expand=True, fill='both')

tk.Label(frame, text="选择Word文档:").pack(anchor='w')
entry_path = tk.Entry(frame, width=50)
entry_path.pack(side='left', fill='x', expand=True, padx=(0, 5))

btn_browse = tk.Button(frame, text="浏览", command=select_file)
btn_browse.pack(side='left')

btn_extract = tk.Button(root, text="提取内容", command=extract_content)
btn_extract.pack(pady=10)

status_label = tk.Label(root, text="")
status_label.pack(pady=10)

# 说明文本
instructions = """
使用说明：
1. 点击"浏览"按钮选择Word文档
2. 点击"提取内容"按钮开始提取
3. 提取的内容将保存为同名的txt文件
4. 提取的内容将保留：
   - 所有级别的标题及其序号
   - 所有正文内容
   - 所有表格内容（保持原始位置）
"""
tk.Label(root, text=instructions, justify='left', wraplength=550).pack(pady=10)

root.mainloop() 
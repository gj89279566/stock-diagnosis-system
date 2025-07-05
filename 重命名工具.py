import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

class RenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量重命名工具")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        tk.Button(self.root, text="选择图片文件", command=self.select_files).pack(pady=10)

        self.file_list = tk.Listbox(self.root, height=10)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=10)

        tk.Label(self.root, text="重命名前缀（如 image）:").pack()
        self.entry_prefix = tk.Entry(self.root)
        self.entry_prefix.pack(pady=5)

        tk.Button(self.root, text="开始重命名", command=self.rename_files).pack(pady=10)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.bmp")])
        self.file_list.delete(0, tk.END)
        for f in files:
            self.file_list.insert(tk.END, f)

    def rename_files(self):
        prefix = self.entry_prefix.get().strip()
        files = self.file_list.get(0, tk.END)

        if not files:
            messagebox.showwarning("提示", "请先选择图片文件")
            return
        if not prefix:
            messagebox.showwarning("提示", "请输入文件名前缀")
            return

        for index, old_path_str in enumerate(files, start=1):
            old_path = Path(old_path_str)
            new_name = f"{prefix}_{index}{old_path.suffix}"
            new_path = old_path.parent / new_name
            try:
                old_path.rename(new_path)
                print(f"重命名：{old_path.name} -> {new_name}")
                with open("rename_log.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"{old_path.name} -> {new_name}\n")
            except Exception as e:
                messagebox.showerror("错误", f"重命名失败：{e}")
                return

        messagebox.showinfo("完成", "所有图片已重命名完成！")
        self.file_list.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = RenameApp(root)
    root.mainloop()
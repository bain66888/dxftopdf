import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import sys

class DXFConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("服装 CAD DXF 转 PDF 工具 (内置引擎版)")
        self.root.geometry("650x400")
        self.root.resizable(False, False)

        self.dxf_files = []
        self.inkscape_path = self.auto_find_inkscape()

        self.create_widgets()

    def auto_find_inkscape(self):
        """核心修改：优先寻找打包集成在软件内部的 Inkscape 引擎"""
        # 1. 如果是通过 PyInstaller 打包运行的环境
        if hasattr(sys, '_MEIPASS'):
            internal_path = os.path.join(sys._MEIPASS, "Inkscape", "bin", "inkscape.exe")
            if os.path.exists(internal_path):
                return internal_path

        # 2. 检查当前 .exe 同级目录下是否存在 Inkscape 文件夹（绿色版目录）
        current_dir = os.path.dirname(sys.argv[0])
        local_path = os.path.join(current_dir, "Inkscape", "bin", "inkscape.exe")
        if os.path.exists(local_path):
            return local_path

        # 3. 兜底方案：检查电脑本地默认安装路径
        common_paths = [
            r"C:\Program Files\Inkscape\bin\inkscape.exe",
            r"C:\Program Files\Inkscape\inkscape.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return ""

    def create_widgets(self):
        # ---- 1. Inkscape 路径设置 ----
        path_frame = tk.LabelFrame(self.root, text=" 1. 核心渲染引擎配置 (Inkscape) ", padding=10)
        path_frame.pack(fill="x", padx=15, pady=10)

        is_internal = " (已完美集成在软件内部)" if "bin" in self.inkscape_path else ""
        self.lbl_inkscape = tk.Label(path_frame, text="引擎状态: " + ("已就绪" + is_internal if self.inkscape_path else "未找到，请手动选择"))
        self.lbl_inkscape.config(fg="green" if self.inkscape_path else "red")
        self.lbl_inkscape.pack(anchor="w")

        entry_frame = tk.Frame(path_frame)
        entry_frame.pack(fill="x", pady=5)

        self.ent_inkscape = tk.Entry(entry_frame, width=60)
        self.ent_inkscape.insert(0, self.inkscape_path)
        self.ent_inkscape.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse_ink = tk.Button(entry_frame, text="浏览...", command=self.browse_inkscape)
        btn_browse_ink.pack(side="right")

        # ---- 2. 文件选择区 ----
        file_frame = tk.LabelFrame(self.root, text=" 2. 选择服装 DXF 文件 (支持多选) ", padding=10)
        file_frame.pack(fill="both", expand=True, padx=15, pady=5)

        btn_select_dxf = tk.Button(file_frame, text="添加 DXF 文件", command=self.browse_dxf, bg="#4CAF50", fg="white")
        btn_select_dxf.pack(anchor="w", pady=(0, 5))

        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED)
        self.file_listbox.pack(fill="both", expand=True)

        # ---- 3. 转换控制区 ----
        control_frame = tk.Frame(self.root, padding=10)
        control_frame.pack(fill="x", padx=15, pady=10)

        self.progress = ttk.Progressbar(control_frame, orient="horizontal", mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_convert = tk.Button(control_frame, text="开始转换", width=15, command=self.start_conversion_thread, bg="#2196F3", fg="white", state="disabled")
        self.btn_convert.pack(side="right")
        
        if self.inkscape_path:
            self.btn_convert.config(state="normal")

    def browse_inkscape(self):
        path = filedialog.askopenfilename(title="选择 inkscape.exe", filetypes=[("执行文件", "*.exe")])
        if path:
            self.inkscape_path = path
            self.ent_inkscape.delete(0, tk.END)
            self.ent_inkscape.insert(0, path)
            self.lbl_inkscape.config(text="引擎状态: 已设置", fg="green")
            self.btn_convert.config(state="normal")

    def browse_dxf(self):
        files = filedialog.askopenfilenames(title="选择 DXF 文件", filetypes=[("CAD DXF 文件", "*.dxf")])
        if files:
            self.dxf_files = list(files)
            self.file_listbox.delete(0, tk.END)
            for f in self.dxf_files:
                self.file_listbox.insert(tk.END, os.path.basename(f))
            if self.inkscape_path:
                self.btn_convert.config(state="normal")

    def start_conversion_thread(self):
        if not self.dxf_files:
            messagebox.showwarning("提示", "请先添加需要转换的 DXF 文件！")
            return
        self.btn_convert.config(state="disabled")
        threading.Thread(target=self.convert_process, daemon=True).start()

    def convert_process(self):
        ink_exe = self.ent_inkscape.get()
        if not os.path.exists(ink_exe):
            messagebox.showerror("错误", "Inkscape 路径无效！")
            self.root.after(0, lambda: self.btn_convert.config(state="normal"))
            return

        total = len(self.dxf_files)
        self.progress["max"] = total
        self.progress["value"] = 0
        success_count = 0
        
        for i, dxf_path in enumerate(self.dxf_files):
            pdf_path = os.path.splitext(dxf_path)[0] + ".pdf"
            cmd = [ink_exe, dxf_path, f"--export-filename={pdf_path}"]
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(cmd, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    success_count += 1
            except Exception as e:
                print(f"转换失败: {str(e)}")
            self.root.after(0, lambda v=i+1: self.set_progress(v))

        messagebox.showinfo("完成", f"批量转换结束！\n成功: {success_count}/{total}")
        self.root.after(0, lambda: self.btn_convert.config(state="normal"))

    def set_progress(self, value):
        self.progress["value"] = value

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = DXFConverterApp(root)
    root.mainloop()

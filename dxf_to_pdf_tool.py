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
        self.root.geometry("650x350")  # 砍掉一行配置后，高度收窄，更紧凑
        self.root.resizable(False, False)

        self.dxf_files = []
        # 后台默默寻找引擎，不在界面上展示
        self.inkscape_path = self.auto_find_inkscape()

        self.create_widgets()

    def auto_find_inkscape(self):
        """后台静默寻找打包集成在软件内部的 Inkscape 引擎"""
        if hasattr(sys, '_MEIPASS'):
            internal_path = os.path.join(sys._MEIPASS, "Inkscape", "bin", "inkscape.exe")
            if os.path.exists(internal_path):
                return internal_path

        current_dir = os.path.dirname(sys.argv[0])
        local_path = os.path.join(current_dir, "Inkscape", "bin", "inkscape.exe")
        if os.path.exists(local_path):
            return local_path

        common_paths = [
            r"C:\Program Files\Inkscape\bin\inkscape.exe",
            r"C:\Program Files\Inkscape\inkscape.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return ""

    def create_widgets(self):
        # ---- 1. 底部转换控制区 (固定在最下方，确保有开始转换按钮) ----
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side="bottom", fill="x", padx=15, pady=10)

        self.progress = ttk.Progressbar(control_frame, orient="horizontal", mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # 如果后台没找到引擎，默认禁用按钮
        btn_state = "normal" if self.inkscape_path else "disabled"
        self.btn_convert = tk.Button(control_frame, text="开始转换", width=15, height=1, 
                                     command=self.start_conversion_thread, bg="#2196F3", fg="white", state=btn_state)
        self.btn_convert.pack(side="right")

        # ---- 2. 中间文件选择区 (撑满剩下的上方所有空间) ----
        file_frame = ttk.LabelFrame(self.root, text=" 选择服装 DXF 文件 (支持多选) ", padding=10)
        file_frame.pack(side="top", fill="both", expand=True, padx=15, pady=15)

        btn_select_dxf = tk.Button(file_frame, text="添加 DXF 文件", command=self.browse_dxf, bg="#4CAF50", fg="white")
        btn_select_dxf.pack(anchor="w", pady=(0, 5))

        # 带滚动条的文件列表
        scrollbar = tk.Scrollbar(file_frame)
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.file_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.file_listbox.yview)

    def browse_dxf(self):
        files = filedialog.askopenfilenames(title="选择 DXF 文件", filetypes=[("CAD DXF 文件", "*.dxf")])
        if files:
            self.dxf_files = list(files)
            self.file_listbox.delete(0, tk.END)
            for f in self.dxf_files:
                self.file_listbox.insert(tk.END, os.path.basename(f))
            
            # 安全保障：如果添加了文件且后台引擎就绪，确保激活按钮
            if self.inkscape_path:
                self.btn_convert.config(state="normal")

    def start_conversion_thread(self):
        if not self.inkscape_path:
            messagebox.showerror("错误", "未检测到内置转换引擎，请确保打包完整！")
            return

        if not self.dxf_files:
            messagebox.showwarning("提示", "请先添加需要转换的 DXF 文件！")
            return

        self.btn_convert.config(state="disabled")
        self.progress["maximum"] = len(self.dxf_files)
        self.progress["value"] = 0
        
        threading.Thread(target=self.convert_process, args=(self.inkscape_path,), daemon=True).start()

    def convert_process(self, ink_exe):
        total = len(self.dxf_files)
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

        self.root.after(0, lambda: self.show_finish_message(success_count, total))

    def set_progress(self, value):
        self.progress["value"] = value

    def show_finish_message(self, success, total):
        messagebox.showinfo("完成", f"批量转换结束！\n成功: {success}/{total}")
        self.btn_convert.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = DXFConverterApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
from collections import defaultdict


class SSHLogAnalyzer:
    def __init__(self):
        self.all_attempts = defaultdict(int)
        self.failed_attempts = defaultdict(list)
        self.success_logins = set()
        self.user_dict = set()
        self.password_attempts = defaultdict(int)

    def analyze(self, log_path):
        ssh_pattern = re.compile(
            r'(?P<status>Failed|Accepted) password for (?P<user>(invalid user )?(\S+)) from (?P<ip>\d+\.\d+\.\d+\.\d+)'
        )

        with open(log_path, 'r') as f:
            for line in f:
                match = ssh_pattern.search(line)
                if match:
                    groups = match.groupdict()
                    ip = groups['ip']
                    user = groups['user'].replace('invalid user ', '')

                    self.user_dict.add(user)
                    self.all_attempts[ip] += 1

                    if groups['status'] == 'Failed':
                        self.failed_attempts[ip].append(user)
                        # 密码提取（注意：实际日志中密码不可见，这里只是演示模式）
                        passwd_match = re.search(r'password\s+for\s+(\S+)\s+from\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if passwd_match:
                            self.password_attempts[passwd_match.group(1)] += 1
                    else:
                        self.success_logins.add(ip)


class LogAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH日志分析工具 v1.0")
        self.analyzer = SSHLogAnalyzer()

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        # 文件选择区域
        self.file_frame = ttk.LabelFrame(self.root, text="日志文件")
        self.btn_open = ttk.Button(self.file_frame, text="打开日志文件", command=self.open_file)
        self.lbl_file = ttk.Label(self.file_frame, text="未选择文件")

        # 结果显示区域
        self.notebook = ttk.Notebook(self.root)

        # SSH爆破分析标签页
        self.tab_ssh = ttk.Frame(self.notebook)
        self.tree_ssh = ttk.Treeview(self.tab_ssh, columns=('IP', '尝试次数', '成功登录'), show='headings')
        self.tree_ssh.heading('IP', text='攻击IP')
        self.tree_ssh.heading('尝试次数', text='尝试次数')
        self.tree_ssh.heading('成功登录', text='是否成功')

        # 用户名字典标签页
        self.tab_users = ttk.Frame(self.notebook)
        self.tree_users = ttk.Treeview(self.tab_users, columns=('账号', '密码尝试次数', '是否攻击成功'), show='headings')
        self.tree_users.heading('账号', text='账号')
        self.tree_users.heading('密码尝试次数', text='密码尝试次数')
        self.tree_users.heading('是否攻击成功', text='是否攻击成功')

        # 拓展功能预留
        self.tab_extra = ttk.Frame(self.notebook)
        self.lbl_extra = ttk.Label(self.tab_extra, text="待开发功能区域")

        # 开始分析按钮
        self.btn_analyze = ttk.Button(self.root, text="开始分析", command=self.start_analysis)

        # 警告栏
        self.warning_label = ttk.Label(self.root, text="警告: ", foreground="red")

    def setup_layout(self):
        # 文件选择布局
        self.file_frame.pack(padx=10, pady=5, fill=tk.X)
        self.btn_open.pack(side=tk.LEFT, padx=5)
        self.lbl_file.pack(side=tk.LEFT)

        # 开始分析按钮布局
        self.btn_analyze.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)

        # 标签页布局
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        self.notebook.add(self.tab_ssh, text='SSH攻击分析')
        self.tree_ssh.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.notebook.add(self.tab_users, text='用户名字典')
        self.tree_users.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.notebook.add(self.tab_extra, text='拓展功能')
        self.lbl_extra.pack(padx=10, pady=10)

        # 警告栏布局
        self.warning_label.pack(side=tk.BOTTOM, fill=tk.X)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
        if file_path:
            try:
                self.analyzer.analyze(file_path)
                self.lbl_file.config(text=file_path)
            except Exception as e:
                messagebox.showerror("错误", f"文件解析失败: {str(e)}")

    def start_analysis(self):
        if self.lbl_file.cget("text") == "未选择文件":
            self.warning_label.config(text="警告: 请先选择一个日志文件")
        else:
            self.warning_label.config(text="警告: ")
            self.show_results()

    def show_results(self):
        # 清空旧数据
        self.tree_ssh.delete(*self.tree_ssh.get_children())
        self.tree_users.delete(*self.tree_users.get_children())

        # 显示攻击IP
        for ip, attempts in self.analyzer.all_attempts.items():
            success = "是" if ip in self.analyzer.success_logins else "否"
            item = self.tree_ssh.insert('', 'end', values=(ip, attempts, success))
            if ip in self.analyzer.success_logins:
                self.tree_ssh.item(item, tags=('success',))
            else:
                self.tree_ssh.item(item, tags=('failed',))

        # 配置标签样式
        self.tree_ssh.tag_configure('success', foreground='green')
        self.tree_ssh.tag_configure('failed', foreground='red')

        # 显示用户名字典
        for user in self.analyzer.user_dict:
            failed_count = len(self.analyzer.failed_attempts.get(user, []))
            success_count = 1 if user in self.analyzer.password_attempts else 0
            total_attempts = failed_count + success_count
            success = "是" if failed_count == 0 else "否"
            item = self.tree_users.insert('', 'end', values=(user, total_attempts, success))
            if failed_count == 0:
                self.tree_users.item(item, tags=('success',))
            else:
                self.tree_users.item(item, tags=('failed',))

        # 配置标签样式
        self.tree_users.tag_configure('success', foreground='green')
        self.tree_users.tag_configure('failed', foreground='red')


if __name__ == "__main__":
    root = tk.Tk()
    app = LogAnalyzerApp(root)
    root.geometry("800x600")
    root.mainloop()

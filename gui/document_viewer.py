"""
文档查看器 - 用于在登录界面查看系统文档
"""

import customtkinter as ctk
from tkinter import ttk
from pathlib import Path
from typing import Optional
from utils.logger import Logger


class DocumentViewer:
    """文档查看窗口类"""
    
    BUPT_BLUE = "#003087"
    BUPT_LIGHT_BLUE = "#0066CC"
    
    def __init__(self, parent):
        """
        初始化文档查看窗口
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
        
        # 创建窗口
        self.window = ctk.CTkToplevel(parent)
        self.window.title("系统文档")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        self.window.transient(parent)
        
        # 居中显示
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"900x700+{x}+{y}")
        
        # 创建界面
        self.create_widgets()
        
        # 默认显示 README
        self.load_document("README.md")
        
        Logger.info("文档查看窗口已打开")
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 主容器
        main_frame = ctk.CTkFrame(self.window, fg_color="white")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        toolbar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        toolbar_frame.pack(fill="x", pady=(0, 10))
        
        # 文档选择标签
        doc_label = ctk.CTkLabel(
            toolbar_frame,
            text="选择文档：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE
        )
        doc_label.pack(side="left", padx=(0, 10))
        
        # 文档选择下拉框
        self.doc_var = ctk.StringVar(value="README.md")
        doc_options = [
            "README.md - 项目说明",
            "使用指南.md - 使用指南",
            "项目总结.md - 项目总结",
            "队友对接指南.md - 队友对接指南",
            "跨机器测试指南.md - 跨机器测试指南"
        ]
        
        doc_menu = ctk.CTkOptionMenu(
            toolbar_frame,
            values=doc_options,
            variable=self.doc_var,
            font=("Microsoft YaHei UI", 13),
            fg_color=self.BUPT_BLUE,
            button_color=self.BUPT_BLUE,
            button_hover_color=self.BUPT_LIGHT_BLUE,
            command=self.on_document_selected,
            width=300
        )
        doc_menu.pack(side="left", padx=(0, 10))
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            toolbar_frame,
            text="🔄 刷新",
            width=80,
            height=30,
            font=("Microsoft YaHei UI", 12),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self.refresh_document
        )
        refresh_btn.pack(side="left", padx=(0, 10))
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            toolbar_frame,
            text="关闭",
            width=80,
            height=30,
            font=("Microsoft YaHei UI", 12),
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=self.window.destroy
        )
        close_btn.pack(side="right")
        
        # 文档内容区域（使用 Text 组件支持滚动和格式化）
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True)
        
        # 使用 Text 组件显示 Markdown 内容（简化版，不渲染 Markdown）
        self.text_widget = ctk.CTkTextbox(
            content_frame,
            font=("Consolas", 11),
            wrap="word",
            fg_color="white",
            text_color="black"
        )
        self.text_widget.pack(fill="both", expand=True)
        
        # 状态栏
        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=30)
        status_frame.pack(fill="x", pady=(10, 0))
        status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="就绪",
            font=("Microsoft YaHei UI", 11),
            text_color="gray",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10)
    
    def on_document_selected(self, value: str):
        """文档选择改变时的回调"""
        # 从选项文本中提取文件名
        doc_name = value.split(" - ")[0]
        self.load_document(doc_name)
    
    def load_document(self, doc_name: str):
        """加载文档内容"""
        try:
            # 确定文档路径
            if doc_name == "README.md":
                doc_path = Path("README.md")
            elif doc_name == "使用指南.md":
                doc_path = Path("docs/使用指南.md")
            elif doc_name == "项目总结.md":
                doc_path = Path("docs/项目总结.md")
            elif doc_name == "队友对接指南.md":
                doc_path = Path("docs/队友对接指南.md")
            elif doc_name == "跨机器测试指南.md":
                doc_path = Path("docs/跨机器测试指南.md")
            else:
                self.status_label.configure(text=f"未知文档: {doc_name}")
                return
            
            # 检查文件是否存在
            if not doc_path.exists():
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", f"文档不存在: {doc_path}\n\n请确保文件存在于项目根目录或 docs 目录中。")
                self.status_label.configure(text=f"文档不存在: {doc_path}")
                Logger.warning(f"文档不存在: {doc_path}")
                return
            
            # 读取文件内容
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示内容
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", content)
            
            # 滚动到顶部
            self.text_widget.see("1.0")
            
            # 更新状态
            file_size = doc_path.stat().st_size
            self.status_label.configure(text=f"已加载: {doc_name} ({file_size} 字节)")
            Logger.info(f"文档加载成功: {doc_path}")
            
        except Exception as e:
            error_msg = f"加载文档失败: {str(e)}"
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", error_msg)
            self.status_label.configure(text="加载失败")
            Logger.error(error_msg, exc_info=True)
    
    def refresh_document(self):
        """刷新当前文档"""
        current_doc = self.doc_var.get().split(" - ")[0]
        self.load_document(current_doc)
        self.status_label.configure(text="已刷新")


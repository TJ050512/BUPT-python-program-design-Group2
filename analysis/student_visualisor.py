"""
学生数据结构可视化模块

功能：
- 读取 students.csv 数据。
- 使用 pandas, matplotlib, seaborn 对学生数据进行分析和可视化。
- 直观展示学生数据的属性分布，如年级、性别、状态等。

用法：
python -m analysis.student_visualizer
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils.logger import Logger

# --- 全局绘图配置 ---
# 设置中文字体，确保图表能正确显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # SimHei 是一个常用的黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题
sns.set_theme(style="whitegrid", font='SimHei')

# 定义数据文件路径和图表输出目录
DATA_FILE = r"data\students.csv"
OUTPUT_DIR = Path("analysis_charts")
OUTPUT_DIR.mkdir(exist_ok=True)


class StudentDataVisualizer:
    """学生数据可视化类"""

    def __init__(self, data_path: Path):
        """
        初始化可视化工具，加载数据。

        Args:
            data_path (Path): students.csv 文件的路径。
        """
        try:
            self.df = pd.read_csv(data_path)
            Logger.info(f"成功从 {data_path} 加载了 {len(self.df)} 条学生数据。")
        except FileNotFoundError:
            Logger.error(f"数据文件未找到: {data_path}")
            self.df = None
        except Exception as e:
            Logger.error(f"加载学生数据时出错: {e}")
            self.df = None

    def plot_table_structure(self):
        """图表0：学生表结构示意图 (美化版)"""
        try:
            from graphviz import Digraph
        except ImportError:
            Logger.error("缺少 graphviz 库。请运行 'pip install graphviz' 并确保已安装 Graphviz 系统软件。")
            Logger.warning("跳过表结构示意图生成。")
            return

        if self.df is None:
            Logger.warning("缺少学生数据，跳过表结构示意图生成。")
            return

        # --- 美化配置 ---
        header_bg = "#003087"
        header_font_color = "white"
        subheader_bg = "#E6F0FA"
        row_bg_light = "#FFFFFF"
        row_bg_dark = "#F7F7F7"
        pk_color = "#E53935"

        dot = Digraph('student_table', comment='学生表结构')
        dot.attr('node', shape='none', fontname='SimHei')
        dot.attr(rankdir='LR')

        # --- 使用 HTML 标签构建美化的表格 ---
        # 关键修改：
        # 1. 添加 FIXEDSIZE="FALSE" 让单元格宽度自适应内容。
        # 2. 增加 CELLPADDING 到 "8" 以提供更多内部空间。
        html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="8" FIXEDSIZE="FALSE">'
        
        # 1. 表头
        html_label += f'<TR><TD BGCOLOR="{header_bg}" ALIGN="CENTER" COLSPAN="3"><FONT COLOR="{header_font_color}" POINT-SIZE="18"><B>students (学生表)</B></FONT></TD></TR>'
        
        # 2. 列标题 - 调整字体大小
        html_label += f'<TR><TD BGCOLOR="{subheader_bg}" POINT-SIZE="12"><B>主键</B></TD><TD BGCOLOR="{subheader_bg}" POINT-SIZE="12"><B>字段名 (Field)</B></TD><TD BGCOLOR="{subheader_bg}" POINT-SIZE="12"><B>数据类型 (Type)</B></TD></TR>'

        # 3. 遍历所有字段并生成表格行
        for i, (col, dtype) in enumerate(self.df.dtypes.items()):
            bg_color = row_bg_light if i % 2 == 0 else row_bg_dark
            
            pk_symbol = ''
            if col == 'student_id':
                pk_symbol = f'<FONT COLOR="{pk_color}" POINT-SIZE="12"><B>PK</B></FONT>'

            # 调整内容字体大小
            html_label += f'<TR><TD ALIGN="CENTER" BGCOLOR="{bg_color}">{pk_symbol}</TD><TD ALIGN="LEFT" BGCOLOR="{bg_color}" POINT-SIZE="12">{col}</TD><TD ALIGN="LEFT" BGCOLOR="{bg_color}" POINT-SIZE="12">{str(dtype)}</TD></TR>'

        html_label += '</TABLE>>'
        
        dot.node('struct', label=html_label)

        try:
            output_path = OUTPUT_DIR / "student_table_structure"
            dot.render(output_path, format='png', cleanup=True)
            Logger.info(f"已生成图表：{output_path.name}.png")
        except Exception as e:
            Logger.error(f"生成表结构图失败，请确保 Graphviz 已正确安装并已添加到系统 PATH。错误: {e}")

    def plot_grade_distribution(self):
        """图表1：各年级学生人数分布"""
        if self.df is None or 'grade' not in self.df.columns:
            Logger.warning("缺少学生数据或'grade'列，跳过年级分布图生成。")
            return

        plt.figure(figsize=(10, 6))
        ax = sns.countplot(x='grade', data=self.df, order=sorted(self.df['grade'].unique()), palette='viridis')
        
        plt.title('各年级学生人数分布', fontsize=16)
        plt.xlabel('入学年份', fontsize=12)
        plt.ylabel('学生人数', fontsize=12)
        ax.bar_label(ax.containers[0])  # 在条形图上显示数字
        
        plt.tight_layout()
        save_path = OUTPUT_DIR / "student_grade_distribution.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def plot_gender_distribution(self):
        """图表2：学生性别比例"""
        if self.df is None or 'gender' not in self.df.columns:
            Logger.warning("缺少学生数据或'gender'列，跳过性别比例图生成。")
            return

        gender_counts = self.df['gender'].value_counts()
        
        plt.figure(figsize=(8, 8))
        plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', startangle=90, colors=['#66b3ff','#ff9999'])
        
        plt.title('学生性别比例', fontsize=16)
        plt.ylabel('')  # 隐藏饼图默认的y轴标签
        
        save_path = OUTPUT_DIR / "student_gender_distribution.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def plot_status_distribution(self):
        """图表3：学生状态分布"""
        if self.df is None or 'status' not in self.df.columns:
            Logger.warning("缺少学生数据或'status'列，跳过状态分布图生成。")
            return

        plt.figure(figsize=(8, 5))
        ax = sns.countplot(y='status', data=self.df, palette='coolwarm')

        plt.title('学生状态分布', fontsize=16)
        plt.xlabel('学生人数', fontsize=12)
        plt.ylabel('状态', fontsize=12)
        ax.bar_label(ax.containers[0])

        plt.tight_layout()
        save_path = OUTPUT_DIR / "student_status_distribution.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def run_all(self):
        """运行所有可视化函数"""
        if self.df is not None:
            Logger.info("--- 开始生成学生数据结构可视化图表 ---")
            self.plot_table_structure()
            self.plot_grade_distribution()
            self.plot_gender_distribution()
            self.plot_status_distribution()
            Logger.info(f"--- 所有图表已生成并保存至目录: {OUTPUT_DIR} ---")
        else:
            Logger.error("由于数据加载失败，无法生成任何图表。")


if __name__ == "__main__":
    visualizer = StudentDataVisualizer(DATA_FILE)
    visualizer.run_all()
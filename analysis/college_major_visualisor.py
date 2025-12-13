"""
学院-专业学生数量可视化模块

功能：
- 读取 students.csv 和 colleges.csv 数据。
- 使用 pandas, matplotlib, seaborn 对数据进行分析和可视化。
- 直观展示每个学院下，各个专业的具体学生数量。

用法：
python -m analysis.college_major_visualizer
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import Logger

# --- 全局绘图配置 ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font='SimHei')

# 定义数据文件路径和图表输出目录
STUDENTS_FILE = project_root / "data" / "students.csv"
COLLEGES_FILE = project_root / "data" / "colleges.csv"
OUTPUT_DIR = project_root / "analysis_charts"
OUTPUT_DIR.mkdir(exist_ok=True)


class CollegeMajorVisualizer:
    """学院-专业学生数量可视化类"""

    def __init__(self, students_path: Path, colleges_path: Path):
        """
        初始化可视化工具，加载数据。
        """
        try:
            self.df_students = pd.read_csv(students_path)
            self.df_colleges = pd.read_csv(colleges_path)
            Logger.info(f"成功加载 {len(self.df_students)} 条学生数据和 {len(self.df_colleges)} 条学院数据。")
        except FileNotFoundError as e:
            Logger.error(f"数据文件未找到: {e}")
            self.df_students = None
            self.df_colleges = None
        except Exception as e:
            Logger.error(f"加载数据时出错: {e}")
            self.df_students = None
            self.df_colleges = None

    def plot_student_count_by_major(self):
        """
        图表：各学院-专业学生数量分布 (分面图)
        为每个学院创建一个子图，展示其下各专业的学生人数。
        """
        if self.df_students is None or self.df_colleges is None:
            Logger.warning("缺少学生或学院数据，跳过图表生成。")
            return

        # 1. 合并学生数据和学院数据，以获取学院全名
        merged_df = pd.merge(
            self.df_students,
            self.df_colleges[['college_code', 'name']],
            on='college_code',
            how='left'
        )
        # 将合并后的学院名列重命名，以防混淆
        merged_df.rename(columns={'name_y': 'college_name', 'name_x': 'student_name'}, inplace=True)

        # 2. 按学院和专业分组，并计算学生数量
        major_counts = merged_df.groupby(['college_name', 'major']).size().reset_index(name='student_count')

        # 3. 使用 catplot 创建分面网格图
        g = sns.catplot(
            data=major_counts,
            kind='bar',
            y='major',
            x='student_count',
            col='college_name',  # 关键：按学院分面，每个学院一个子图
            col_wrap=2,          # 每行最多显示2个学院的子图
            height=5,
            aspect=1.8,
            sharey=False,        # 不同学院的Y轴（专业名）不共享
            palette='mako'
        )

        # 4. 对图表进行精细化调整
        g.fig.suptitle('各学院专业学生数量分布图', y=1.03, fontsize=20, weight='bold')
        g.set_titles("学院: {col_name}", size=14)
        g.set_axis_labels("学生人数", "专业名称")
        
        # 为每个子图的条形添加数值标签
        for ax in g.axes.flat:
            ax.bar_label(ax.containers[0], fmt='%d', padding=3)

        plt.tight_layout(rect=[0, 0, 1, 1])
        
        # 5. 保存图表
        save_path = OUTPUT_DIR / "student_count_by_major_and_college.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close(g.fig)

    def run(self):
        """运行所有可视化函数"""
        if self.df_students is not None:
            Logger.info("--- 开始生成学院-专业学生数量可视化图表 ---")
            self.plot_student_count_by_major()
            Logger.info(f"--- 图表已生成并保存至目录: {OUTPUT_DIR} ---")
        else:
            Logger.error("由于数据加载失败，无法生成任何图表。")


if __name__ == "__main__":
    visualizer = CollegeMajorVisualizer(STUDENTS_FILE, COLLEGES_FILE)
    visualizer.run()
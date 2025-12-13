"""
教师数据结构可视化模块

功能：
- 读取 teachers.csv 数据。
- 使用 pandas, matplotlib, seaborn 对教师数据进行分析和可视化。
- 直观展示教师数据的属性分布，如职称、所属学院、性别等。

用法：
python -m analysis.teacher_visualizer
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .table_drawer import draw_table_structure

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
TEACHERS_FILE = project_root / "data" / "teachers.csv"
OUTPUT_DIR = project_root / "analysis_charts"
OUTPUT_DIR.mkdir(exist_ok=True)


class TeacherDataVisualizer:
    """教师数据可视化类"""

    def __init__(self, data_path: Path):
        """
        初始化可视化工具，加载数据。
        """
        try:
            self.df = pd.read_csv(data_path)
            Logger.info(f"成功从 {data_path} 加载了 {len(self.df)} 条教师数据。")
        except FileNotFoundError:
            Logger.error(f"数据文件未找到: {data_path}")
            self.df = None
        except Exception as e:
            Logger.error(f"加载教师数据时出错: {e}")
            self.df = None

    def plot_table_structure(self):
        """图表0：教师表结构示意图"""
        draw_table_structure(
            df=self.df,
            table_name="teachers (教师表)",
            pk_column="teacher_id",
            output_dir=OUTPUT_DIR,
            file_stem="teacher_table_structure"
        )

    def plot_department_distribution(self):
        """图表1：各学院教师数量分布"""
        if self.df is None or 'department' not in self.df.columns:
            Logger.warning("缺少教师数据或'department'列，跳过学院分布图生成。")
            return

        plt.figure(figsize=(12, 8))
        order = self.df['department'].value_counts().index
        ax = sns.countplot(y='department', data=self.df, order=order, palette='crest_r')

        plt.title('各学院教师数量分布', fontsize=16, weight='bold')
        plt.xlabel('教师人数', fontsize=12)
        plt.ylabel('学院/部门', fontsize=12)
        ax.bar_label(ax.containers[0], fmt='%d', padding=3)

        plt.tight_layout()
        save_path = OUTPUT_DIR / "teacher_department_distribution.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def plot_title_distribution(self):
        """图表2：教师职称结构"""
        if self.df is None or 'title' not in self.df.columns:
            Logger.warning("缺少教师数据或'title'列，跳过职称分布图生成。")
            return

        plt.figure(figsize=(10, 6))
        order = self.df['title'].value_counts().index
        ax = sns.countplot(x='title', data=self.df, order=order, palette='flare')

        plt.title('教师职称结构分布', fontsize=16, weight='bold')
        plt.xlabel('职称', fontsize=12)
        plt.ylabel('教师人数', fontsize=12)
        ax.bar_label(ax.containers[0], fmt='%d')

        plt.tight_layout()
        save_path = OUTPUT_DIR / "teacher_title_distribution.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def plot_gender_distribution(self):
        """图表3：教师性别比例"""
        if self.df is None or 'gender' not in self.df.columns:
            Logger.warning("缺少教师数据或'gender'列，跳过性别比例图生成。")
            return

        gender_counts = self.df['gender'].value_counts()

        plt.figure(figsize=(8, 8))
        plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', startangle=90,
                colors=['#66b3ff', '#ff9999', '#99ff99'], textprops={'fontsize': 14})

        plt.title('教师性别比例', fontsize=16, weight='bold')
        plt.ylabel('')

        save_path = OUTPUT_DIR / "teacher_gender_distribution.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def plot_title_composition_by_department(self):
        """图表4：各学院教师职称构成 (堆叠条形图)"""
        if self.df is None or 'department' not in self.df.columns or 'title' not in self.df.columns:
            Logger.warning("缺少教师数据或相关列，跳过职称构成图生成。")
            return

        # 1. 按学院和职称分组计数
        composition = self.df.groupby(['department', 'title']).size().unstack(fill_value=0)

        # 2. 定义职称的逻辑顺序，用于图例排序
        title_order = ['讲师', '副教授', '教授', '副研究员', '研究员']
        # 筛选出数据中实际存在的职称，并按预定顺序排序
        ordered_titles = [t for t in title_order if t in composition.columns]
        composition = composition[ordered_titles]

        # 3. 按各学院总教师数降序排列，使图表更美观
        composition['total'] = composition.sum(axis=1)
        composition = composition.sort_values('total', ascending=False).drop('total', axis=1)

        # 4. 绘制堆叠条形图
        ax = composition.plot(
            kind='bar',
            stacked=True,
            figsize=(14, 8),
            colormap='viridis',
            width=0.8
        )

        plt.title('各学院教师职称构成', fontsize=18, weight='bold')
        plt.xlabel('学院/部门', fontsize=12)
        plt.ylabel('教师人数', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='职称')
        plt.tight_layout()

        # 5. 保存图表
        save_path = OUTPUT_DIR / "teacher_title_composition.png"
        plt.savefig(save_path)
        Logger.info(f"已生成图表：{save_path.name}")
        plt.close()

    def run_all(self):
        """运行所有可视化函数"""
        if self.df is not None:
            Logger.info("--- 开始生成教师数据可视化图表 ---")
            self.plot_table_structure()
            self.plot_department_distribution()
            self.plot_title_distribution()
            self.plot_gender_distribution()
            self.plot_title_composition_by_department() # 新增的函数调用
            Logger.info(f"--- 所有图表已生成并保存至目录: {OUTPUT_DIR} ---")
        else:
            Logger.error("由于数据加载失败，无法生成任何图表。")


if __name__ == "__main__":
    visualizer = TeacherDataVisualizer(TEACHERS_FILE)
    visualizer.run_all()
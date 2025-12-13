"""
数据可视化模块

功能：
- 连接到 SQLite 数据库 (bupt_teaching.db)。
- 使用 pandas, matplotlib, seaborn 对数据进行分析和可视化。
- 全面展示数据库内容的丰富性、数据逻辑的合理性以及 data_simulator.py 的生成效果。

用法：
python -m analysis.visualizer
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger

# --- 全局绘图配置 ---
# 设置中文字体，确保图表能正确显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # SimHei 是一个常用的黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题
sns.set_theme(style="whitegrid", font='SimHei')

# 创建一个目录来保存生成的图表
output_dir = project_root / "analysis_charts"
output_dir.mkdir(exist_ok=True)


class DataVisualizer:
    """
    数据可视化类，封装了所有绘图功能。
    """
    def __init__(self, db_path: str):
        """
        初始化，连接数据库并加载核心数据到 pandas DataFrame。
        """
        self.db_path = db_path
        self.db = Database(db_path)
        self.db.connect()  # 只调用连接方法，不接收返回值
        self.conn = self.db.conn  # 直接获取 Database 对象内部的连接属性
        Logger.info(f"已连接到数据库: {db_path}")

        # 使用 pandas 加载核心数据表，便于分析
        self.df_students = pd.read_sql_query("SELECT * FROM students", self.conn)
        self.df_teachers = pd.read_sql_query("SELECT * FROM teachers", self.conn)
        self.df_courses = pd.read_sql_query("SELECT * FROM courses", self.conn)
        self.df_offerings = pd.read_sql_query("SELECT * FROM course_offerings", self.conn)
        self.df_enrollments = pd.read_sql_query("SELECT * FROM enrollments", self.conn)
        self.df_grades = pd.read_sql_query("SELECT * FROM grades", self.conn)
        self.df_classrooms = pd.read_sql_query("SELECT * FROM classrooms", self.conn)
        self.df_sessions = pd.read_sql_query("SELECT * FROM offering_sessions", self.conn)
        self.df_timeslots = pd.read_sql_query("SELECT * FROM time_slots", self.conn)
        Logger.info("核心数据已加载到 Pandas DataFrames。")

    def close(self):
        """关闭数据库连接"""
        self.db.close()
        Logger.info("数据库连接已关闭。")

    def plot_student_distribution_by_college(self):
        """
        图表1：各学院学生人数分布
        - 优点展示：直观展示了 data_simulator.py 生成的学生数据规模和在各学院间的均衡分布。
        """
        plt.figure(figsize=(12, 8))
        
        # --- 修改开始 ---
        # 优化合并逻辑：直接从数据库一次性查询出带有学院名称的学生信息
        query = """
        SELECT
            s.student_id,
            c.name AS college_name
        FROM students s
        JOIN majors m ON s.major_id = m.major_id
        JOIN colleges c ON m.college_code = c.college_code
        """
        student_college_info = pd.read_sql_query(query, self.conn)

        if student_college_info.empty:
            Logger.warning("无法获取学生与学院的关联信息，跳过图表1的生成。")
            return

        ax = sns.countplot(y=student_college_info['college_name'], order=student_college_info['college_name'].value_counts().index, palette='viridis')
        # --- 修改结束 ---
        
        plt.title('图1：各学院学生人数分布', fontsize=16)
        plt.xlabel('学生人数', fontsize=12)
        plt.ylabel('学院', fontsize=12)
        ax.bar_label(ax.containers[0]) # 在条形图上显示数字
        plt.tight_layout()
        plt.savefig(output_dir / "1_student_distribution_by_college.png")
        Logger.info("已生成图表：1_student_distribution_by_college.png")

    def plot_teacher_distribution_by_title(self):
        """
        图表2：教师职称分布
        - 优点展示：体现了教师数据的多样性和真实性，模拟了高校中不同职称教师的构成比例。
        """
        plt.figure(figsize=(10, 6))
        ax = sns.countplot(x=self.df_teachers['title'], order=self.df_teachers['title'].value_counts().index, palette='plasma')
        plt.title('图2：教师职称分布', fontsize=16)
        plt.xlabel('职称', fontsize=12)
        plt.ylabel('教师人数', fontsize=12)
        ax.bar_label(ax.containers[0])
        plt.tight_layout()
        plt.savefig(output_dir / "2_teacher_distribution_by_title.png")
        Logger.info("已生成图表：2_teacher_distribution_by_title.png")

    def plot_course_distribution_by_type(self):
        """
        图表3：课程类型分布
        - 优点展示：清晰展示了课程库中“公共必修”、“专业必修”、“通识选修”等各类课程的比例，
          反映了数据库课程体系设计的完整性。
        """
        plt.figure(figsize=(10, 8))
        course_type_counts = self.df_courses['course_type'].value_counts()
        plt.pie(course_type_counts, labels=course_type_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('Set2'))
        plt.title('图3：课程类型分布', fontsize=16)
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(output_dir / "3_course_distribution_by_type.png")
        Logger.info("已生成图表：3_course_distribution_by_type.png")

    def plot_overall_grade_distribution(self):
        """
        图表4：全校学生总评成绩分布
        - 优点展示：这是衡量数据仿真质量的关键图表。一个近似正态分布的成绩曲线，
          说明 data_simulator.py 生成的成绩数据非常符合真实世界的统计规律。
        """
        plt.figure(figsize=(12, 7))
        sns.histplot(self.df_grades['score'], bins=40, kde=True, color='skyblue')
        plt.title('图4：全校学生总评成绩分布', fontsize=16)
        plt.xlabel('分数', fontsize=12)
        plt.ylabel('频数', fontsize=12)
        plt.axvline(self.df_grades['score'].mean(), color='r', linestyle='--', label=f'平均分: {self.df_grades["score"].mean():.2f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "4_overall_grade_distribution.png")
        Logger.info("已生成图表：4_overall_grade_distribution.png")

    def plot_avg_gpa_by_major(self):
        """
        图表5：各专业平均GPA对比
        - 优点展示：体现了数据分析的潜力。通过聚合分析，可以模拟出不同专业间“学业表现”的差异，
          为教学管理提供决策支持。
        """
        # 优化合并逻辑：直接将成绩表与学生表通过 student_id 合并
        grades_with_major = pd.merge(self.df_grades, self.df_students[['student_id', 'major']], on='student_id', how='left')
        
        avg_gpa = grades_with_major.groupby('major')['gpa'].mean().sort_values(ascending=False)
        
        plt.figure(figsize=(12, 10))
        
        # --- 修改开始：补充完整的绘图和保存代码 ---
        ax = sns.barplot(y=avg_gpa.index, x=avg_gpa.values, palette='coolwarm')
        plt.title('图5：各专业平均GPA对比', fontsize=16)
        plt.xlabel('平均GPA', fontsize=12)
        plt.ylabel('专业', fontsize=12)
        ax.bar_label(ax.containers[0], fmt='%.2f')
        plt.tight_layout()
        plt.savefig(output_dir / "5_avg_gpa_by_major.png")
        Logger.info("已生成图表：5_avg_gpa_by_major.png")
        # --- 修改结束 ---

    def plot_course_popularity(self, top_n=20):
        """
        图表6：最受欢迎的课程排行 (按选课人数)
        - 优点展示：模拟了真实的选课热度，可以直观地看出哪些课程（尤其是公选课）最受学生欢迎。
        """
        # 合并开课计划和课程信息
        offerings_with_courses = pd.merge(self.df_offerings, self.df_courses, on='course_id')
        
        # 按课程名称聚合选课人数
        course_popularity = offerings_with_courses.groupby('course_name')['current_students'].sum().sort_values(ascending=False).head(top_n)
        
        plt.figure(figsize=(12, 10))
        ax = sns.barplot(y=course_popularity.index, x=course_popularity.values, palette='rocket')
        plt.title(f'图6：最受欢迎的 Top {top_n} 门课程 (按总选课人数)', fontsize=16)
        plt.xlabel('总选课人数', fontsize=12)
        plt.ylabel('课程名称', fontsize=12)
        ax.bar_label(ax.containers[0])
        plt.tight_layout()
        plt.savefig(output_dir / "6_course_popularity.png")
        Logger.info("已生成图表：6_course_popularity.png")

    def plot_classroom_utilization_heatmap(self, semester: str):
        """
        图表7：教室资源利用率热力图 (特定学期)
        - 优点展示：这是项目的核心亮点之一！此图直观展示了排课算法的成果。
          一个分布均匀、冲突少的热力图，证明了 data_simulator.py 中复杂的排课与冲突检测逻辑是成功的。
        """
        # 筛选特定学期的排课数据
        offerings_sem = self.df_offerings[self.df_offerings['semester'] == semester]
        sessions_sem = pd.merge(self.df_sessions, offerings_sem[['offering_id']], on='offering_id')
        
        # 合并节次和教室信息
        utilization_data = pd.merge(sessions_sem, self.df_timeslots, on='slot_id')
        utilization_data = pd.merge(utilization_data, self.df_classrooms[['classroom_id', 'name']], on='classroom_id')
        
        # 创建用于热力图的透视表
        heatmap_data = utilization_data.groupby(['name', 'day_of_week']).size().unstack(fill_value=0)
        
        # 确保所有周一到周五都存在
        for day in range(1, 6):
            if day not in heatmap_data.columns:
                heatmap_data[day] = 0
        heatmap_data = heatmap_data[[1, 2, 3, 4, 5]] # 排序
        heatmap_data.columns = ['周一', '周二', '周三', '周四', '周五']
        
        if heatmap_data.empty:
            Logger.warning(f"学期 {semester} 没有排课数据，无法生成热力图。")
            return

        plt.figure(figsize=(15, 20))
        sns.heatmap(heatmap_data, cmap='YlGnBu', annot=True, fmt='d', linewidths=.5)
        plt.title(f'图7：教室资源利用率热力图 (学期: {semester})', fontsize=16)
        plt.xlabel('星期', fontsize=12)
        plt.ylabel('教室', fontsize=12)
        plt.tight_layout()
        plt.savefig(output_dir / "7_classroom_utilization_heatmap.png")
        Logger.info("已生成图表：7_classroom_utilization_heatmap.png")

    def plot_curriculum_courses_by_major(self):
        """
        图表8：各专业培养方案内课程数量对比
        - 优点展示：展示了培养方案设计的广度和深度，体现了不同专业课程体系的差异。
        """
        query = """
        SELECT
            c.name AS college_name,
            m.name AS major_name,
            COUNT(pc.course_id) AS course_count
        FROM program_courses pc
        JOIN majors m ON pc.major_id = m.major_id
        JOIN colleges c ON m.college_code = c.college_code
        GROUP BY c.name, m.name
        ORDER BY course_count DESC
        """
        df_curriculum = pd.read_sql_query(query, self.conn)

        if df_curriculum.empty:
            Logger.warning("无法获取培养方案课程信息，跳过图表8的生成。")
            return

        plt.figure(figsize=(14, 12))
        ax = sns.barplot(
            data=df_curriculum,
            y='major_name',
            x='course_count',
            hue='college_name',
            dodge=False, # 使用堆叠效果，如果想分组对比，可以设为 True
            palette='tab20'
        )
        plt.title('图表8：各专业培养方案内课程数量对比', fontsize=16)
        plt.xlabel('课程数量', fontsize=12)
        plt.ylabel('专业名称', fontsize=12)
        plt.legend(title='学院', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout(rect=[0, 0, 0.85, 1]) # 调整布局为图例留出空间
        plt.savefig(output_dir / "8_curriculum_courses_by_major.png")
        Logger.info("已生成图表：8_curriculum_courses_by_major.png")

    def plot_course_type_distribution_by_college(self):
        """
        图表9：各学院课程类型分布
        - 优点展示：深入揭示了不同学院的课程设置策略。例如，工科学院可能专业课占比高，
          而人文学院的通识课可能更多，这反映了数据生成的深度和真实性。
        """
        # 假设 courses 表中的 'department' 列对应学院名称
        query = """
        SELECT
            department,
            course_type,
            COUNT(course_id) AS course_count
        FROM courses
        WHERE department IS NOT NULL AND department != ''
        GROUP BY department, course_type
        """
        df_course_types = pd.read_sql_query(query, self.conn)

        if df_course_types.empty:
            Logger.warning("无法获取学院课程类型分布信息，跳过图表9的生成。")
            return

        # 使用 pivot_table 将数据重塑为适合堆叠条形图的格式
        pivot_df = df_course_types.pivot_table(
            index='department',
            columns='course_type',
            values='course_count',
            fill_value=0
        )

        # 按总课程数对学院进行排序，使图表更美观
        pivot_df['total'] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values('total', ascending=False).drop('total', axis=1)

        # 使用 pandas 自带的绘图功能创建堆叠条形图
        ax = pivot_df.plot(
            kind='bar',
            stacked=True,
            figsize=(14, 8),
            colormap='viridis',
            width=0.8
        )

        plt.title('图表9：各学院课程类型分布', fontsize=16)
        plt.xlabel('学院', fontsize=12)
        plt.ylabel('课程数量', fontsize=12)
        plt.xticks(rotation=45, ha='right') # 让学院名称倾斜，避免重叠
        plt.legend(title='课程类型')
        plt.tight_layout()
        plt.savefig(output_dir / "9_course_type_distribution_by_college.png")
        Logger.info("已生成图表：9_course_type_distribution_by_college.png")

    def plot_curriculum_composition_by_major(self):
        """
        图表10：各专业课程构成分布 (按学院分面)
        - 优点展示：这是最深度的课程体系可视化。它清晰地展示了每个专业的课程构成（必修/选修比例），
          并按学院将专业分组，便于横向比较不同专业的培养方案侧重点。
        """
        query = """
        SELECT
            col.name AS college_name,
            m.name AS major_name,
            c.course_type,
            COUNT(c.course_id) AS course_count
        FROM program_courses pc
        JOIN courses c ON pc.course_id = c.course_id
        JOIN majors m ON pc.major_id = m.major_id
        JOIN colleges col ON m.college_code = col.college_code
        GROUP BY col.name, m.name, c.course_type
        ORDER BY col.name, m.name, c.course_type
        """
        df_composition = pd.read_sql_query(query, self.conn)

        if df_composition.empty:
            Logger.warning("无法获取专业课程构成信息，跳过图表10的生成。")
            return

        # 使用 catplot 创建分面网格图，这是展示多维分类数据的利器
        g = sns.catplot(
            data=df_composition,
            kind='bar',
            x='major_name',
            y='course_count',
            hue='course_type',
            col='college_name',  # 关键：按学院分面，每个学院一个子图
            col_wrap=2,          # 每行最多显示2个学院的子图
            height=6,
            aspect=1.5,
            sharex=False,        # 不同学院的X轴（专业名）不共享，避免拥挤
            palette='Set2'
        )

        # 对每个子图进行精细化调整
        g.set_titles("学院: {col_name}")
        g.set_axis_labels("专业名称", "课程数量")
        g.set_xticklabels(rotation=45, ha='right')
        g.despine(left=True)
        g.legend.set_title("课程类型")

        # 调整整体标题
        g.fig.suptitle('图表10：各专业课程构成分布 (按学院分面)', y=1.03, fontsize=16)

        plt.tight_layout(rect=[0, 0, 1, 1])
        plt.savefig(output_dir / "10_curriculum_composition_by_major.png")
        Logger.info("已生成图表：10_curriculum_composition_by_major.png")
        plt.close(g.fig) # 关闭图形，避免在后续绘图中产生干扰

    def run_all_visualizations(self):
        """
        运行所有可视化函数，生成全套图表。
        """
        Logger.info("--- 开始生成全套数据可视化图表 ---")
        self.plot_student_distribution_by_college()
        self.plot_teacher_distribution_by_title()
        self.plot_course_distribution_by_type()
        self.plot_overall_grade_distribution()
        self.plot_avg_gpa_by_major()
        self.plot_course_popularity()
        self.plot_curriculum_composition_by_major()
        
        # 为最新的一个学期生成热力图
        latest_semester = self.df_offerings['semester'].max()
        if pd.notna(latest_semester):
            self.plot_classroom_utilization_heatmap(semester=latest_semester)
        else:
            Logger.warning("未找到任何开课学期，跳过教室利用率热力图的生成。")
        self.plot_curriculum_courses_by_major()
        self.plot_course_type_distribution_by_college()
        Logger.info(f"--- 所有图表已生成并保存至目录: {output_dir.resolve()} ---")


if __name__ == "__main__":
    Logger.init()
    try:
        # 实例化并运行
        visualizer = DataVisualizer(db_path=str(project_root / "data" / "bupt_teaching.db"))
        visualizer.run_all_visualizations()
        visualizer.close()
    except Exception as e:
        Logger.error(f"数据可视化过程中发生错误: {e}", exc_info=True)
        # 提示用户可能需要先生成数据
        db_file = project_root / "data" / "bupt_teaching.db"
        if not db_file.exists() or os.path.getsize(db_file) < 1024: # 如果文件不存在或很小
             Logger.warning("提示：数据库文件不存在或为空。请先运行 data_simulator.py 生成数据。")
             Logger.warning("命令示例: python -m utils.data_simulator all")

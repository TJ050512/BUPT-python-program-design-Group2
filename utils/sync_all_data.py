import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# 导入各个工具模块
try:
    from utils import import_csv
    from utils import import_courses
    from utils import import_curriculum_matrix
    from utils import import_course_offerings
except ImportError:
    # 如果直接作为脚本运行可能导致相对导入问题，尝试动态导入
    import import_csv
    import import_courses
    import import_curriculum_matrix
    import import_course_offerings

def main():
    print("=" * 60)
    print("🚀 开始全量数据同步")
    print("=" * 60)
    print("此脚本将依次运行所有数据导入工具，确保数据库与 CSV/Markdown 文件同步。")
    print()
    
    # 1. 导入学生和教师
    # 这是基础用户数据
    print(f"\n[{'='*20} 步骤 1/4: 导入学生和教师 {'='*20}]")
    try:
        import_csv.main()
    except Exception as e:
        print(f"❌ 步骤 1 失败: {e}")
        return

    # 2. 导入课程和基础培养方案
    # 这会创建课程表、学院表、专业表
    print(f"\n[{'='*20} 步骤 2/4: 导入课程和专业 {'='*20}]")
    try:
        import_courses.main()
    except Exception as e:
        print(f"❌ 步骤 2 失败: {e}")
        return

    # 3. 导入详细课程矩阵
    # 从 Markdown 文件导入详细的培养计划
    print(f"\n[{'='*20} 步骤 3/4: 导入课程矩阵 {'='*20}]")
    try:
        import_curriculum_matrix.import_curriculum_matrix()
    except Exception as e:
        print(f"❌ 步骤 3 失败: {e}")
        return

    # 4. 导入开课计划
    # 依赖于课程和教师数据
    print(f"\n[{'='*20} 步骤 4/4: 导入开课计划 {'='*20}]")
    try:
        import_course_offerings.main()
    except Exception as e:
        print(f"❌ 步骤 4 失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 所有数据同步完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()


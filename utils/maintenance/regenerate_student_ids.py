"""
学号重新生成工具
按照新规则重新生成学生学号：YYYY + TT + CC + NN
- YYYY: 年份（4位）
- TT: 学生类型（21=本科生）
- CC: 班级号（01-99）
- NN: 班内学生编号（01-50）
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# 确保项目根在模块搜索路径中
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger


class StudentIDRegenerator:
    """学号重新生成器"""
    
    def __init__(self, db_path: str = "data/bupt_teaching.db"):
        """初始化"""
        self.db = Database(db_path)
        Logger.info("学号重新生成器初始化完成")
    
    def regenerate_student_ids(self, year: str = "2021", student_type: str = "21", 
                               students_per_class: int = 50):
        """
        重新生成学生学号
        
        Args:
            year: 入学年份，4位数字
            student_type: 学生类型（21=本科生）
            students_per_class: 每个班级的学生人数
        """
        Logger.info("=" * 80)
        Logger.info("开始重新生成学生学号")
        Logger.info(f"规则: {year}年 + {student_type}(本科生) + 班级号(2位) + 学号(2位)")
        Logger.info(f"每班学生数: {students_per_class}人")
        Logger.info("=" * 80)
        
        # 获取所有学生，按当前学号排序
        students = self.db.execute_query(
            "SELECT * FROM students ORDER BY student_id"
        )
        
        if not students:
            Logger.warning("没有找到学生数据")
            return
        
        total_students = len(students)
        total_classes = (total_students + students_per_class - 1) // students_per_class
        
        Logger.info(f"学生总数: {total_students}")
        Logger.info(f"将分配到 {total_classes} 个班级")
        Logger.info("")
        
        # 记录学号映射关系
        id_mapping = []
        
        # 逐个重新分配学号
        for idx, student in enumerate(students, start=1):
            # 计算班级号和班内序号
            class_num = (idx - 1) // students_per_class + 1
            in_class_num = (idx - 1) % students_per_class + 1
            
            # 生成新学号: YYYY + TT + CC + NN
            new_student_id = f"{year}{student_type}{class_num:02d}{in_class_num:02d}"
            
            # 生成新的班级名称（年份+两位数班级号）
            new_class_name = f"{year}{class_num:02d}"
            
            # 生成新的邮箱
            new_email = f"{new_student_id}@bupt.edu.cn"
            
            old_student_id = student['student_id']
            
            # 记录映射
            id_mapping.append({
                'old_id': old_student_id,
                'new_id': new_student_id,
                'name': student['name'],
                'class': new_class_name,
                'class_num': class_num,
                'in_class_num': in_class_num
            })
            
            Logger.debug(f"学生 {idx}/{total_students}: {old_student_id} -> {new_student_id} "
                        f"({student['name']}, {new_class_name}班, 第{in_class_num}号)")
        
        # 显示每个班级的分配情况
        Logger.info("")
        Logger.info("班级分配情况:")
        for class_num in range(1, total_classes + 1):
            class_students = [m for m in id_mapping if m['class_num'] == class_num]
            Logger.info(f"  {year}{class_num:02d}班: {len(class_students)}人 "
                       f"(学号: {year}{student_type}{class_num:02d}01 ~ "
                       f"{year}{student_type}{class_num:02d}{len(class_students):02d})")
        
        Logger.info("")
        
        # 询问用户确认
        print("\n" + "=" * 80)
        print("学号重新生成预览")
        print("=" * 80)
        print(f"将为 {total_students} 名学生重新分配学号，分配到 {total_classes} 个班级")
        print("\n前5个学生示例:")
        for mapping in id_mapping[:5]:
            print(f"  {mapping['old_id']} -> {mapping['new_id']} ({mapping['name']}, "
                  f"{mapping['class']}班)")
        print("\n后5个学生示例:")
        for mapping in id_mapping[-5:]:
            print(f"  {mapping['old_id']} -> {mapping['new_id']} ({mapping['name']}, "
                  f"{mapping['class']}班)")
        
        print("\n" + "=" * 80)
        confirm = input("\n确认执行学号更新？(yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            Logger.warning("用户取消操作")
            print("操作已取消")
            return
        
        # 执行更新
        Logger.info("开始更新数据库...")
        success_count = 0
        fail_count = 0
        
        # 由于学号是主键，需要先临时修改
        # 方案：先加前缀 'TEMP_'，然后再更新为新学号
        try:
            # 第一步：将所有旧学号加上临时前缀
            Logger.info("第一步：添加临时前缀...")
            for student in students:
                old_id = student['student_id']
                temp_id = f"TEMP_{old_id}"
                self.db.execute_query(
                    "UPDATE students SET student_id = ? WHERE student_id = ?",
                    (temp_id, old_id)
                )
            
            # 第二步：更新为新学号和新班级
            Logger.info("第二步：更新为新学号...")
            for mapping in id_mapping:
                try:
                    temp_id = f"TEMP_{mapping['old_id']}"
                    new_id = mapping['new_id']
                    new_class = mapping['class']
                    new_email = f"{new_id}@bupt.edu.cn"
                    
                    self.db.execute_query(
                        """UPDATE students 
                           SET student_id = ?, 
                               class_name = ?, 
                               email = ?,
                               updated_at = ?
                           WHERE student_id = ?""",
                        (new_id, new_class, new_email, 
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         temp_id)
                    )
                    success_count += 1
                    
                except Exception as e:
                    fail_count += 1
                    Logger.error(f"更新学号失败 {mapping['old_id']} -> {mapping['new_id']}: {e}")
            
            Logger.info(f"数据库更新完成: 成功 {success_count} 条, 失败 {fail_count} 条")
            
            # 导出更新后的CSV文件
            self.export_to_csv()
            
            # 保存学号映射文件
            self.save_mapping(id_mapping)
            
            print("\n" + "=" * 80)
            print("✓ 学号重新生成完成！")
            print("=" * 80)
            print(f"✓ 成功更新 {success_count} 个学号")
            print(f"✓ 新学号已保存到数据库")
            print(f"✓ 已导出更新后的 CSV 文件: data/students.csv")
            print(f"✓ 学号映射关系已保存: data/student_id_mapping.csv")
            print("=" * 80)
            
        except Exception as e:
            Logger.error(f"更新过程出错: {e}", exc_info=True)
            print(f"\n✗ 更新失败: {e}")
            print("数据库可能处于不一致状态，请检查日志文件")
    
    def export_to_csv(self, output_file: str = "data/students.csv"):
        """导出学生数据到CSV"""
        Logger.info(f"导出学生数据到: {output_file}")
        
        students = self.db.execute_query("SELECT * FROM students ORDER BY student_id")
        
        if not students:
            Logger.warning("没有学生数据可导出")
            return
        
        # 定义CSV列
        fieldnames = [
            'student_id', 'name', 'password', 'gender', 'birth_date', 
            'major', 'grade', 'class_name', 'enrollment_date', 'status', 
            'email', 'phone', 'created_at', 'updated_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for student in students:
                writer.writerow({k: student.get(k, '') for k in fieldnames})
        
        Logger.info(f"成功导出 {len(students)} 条学生数据")
    
    def save_mapping(self, id_mapping: list, output_file: str = "data/student_id_mapping.csv"):
        """保存学号映射关系"""
        Logger.info(f"保存学号映射到: {output_file}")
        
        fieldnames = ['old_id', 'new_id', 'name', 'class', 'class_num', 'in_class_num']
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(id_mapping)
        
        Logger.info(f"成功保存 {len(id_mapping)} 条映射记录")
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()


def main():
    """主函数"""
    print("=" * 80)
    print("北京邮电大学教学管理系统 - 学号重新生成工具")
    print("=" * 80)
    print()
    print("新学号规则:")
    print("  格式: YYYY + TT + CC + NN")
    print("  - YYYY: 年份（4位）")
    print("  - TT: 学生类型（21=本科生）")
    print("  - CC: 班级号（01-99）")
    print("  - NN: 班内学生编号（01-50）")
    print()
    print("示例: 2021210101 = 2021年 + 本科生 + 01班 + 01号")
    print()
    
    # 初始化日志
    Logger.init()
    
    # 创建重新生成器
    regenerator = StudentIDRegenerator()
    
    try:
        # 执行重新生成
        regenerator.regenerate_student_ids(
            year="2021",
            student_type="21",
            students_per_class=50
        )
        
    except Exception as e:
        Logger.error(f"执行出错: {e}", exc_info=True)
        print(f"\n✗ 执行失败: {e}")
        print("请检查日志文件: logs/app.log")
    
    finally:
        regenerator.close()


if __name__ == "__main__":
    main()


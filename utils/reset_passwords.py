"""
重置CSV导入用户的密码
将所有学生和教师账户的密码重置为已知密码
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.crypto import CryptoUtil
from utils.logger import Logger


def reset_passwords():
    """重置所有用户密码"""
    
    # 初始化日志
    Logger.init()
    
    # 设置新密码
    STUDENT_PASSWORD = "123456"  # 学生统一密码
    TEACHER_PASSWORD = "123456"  # 教师统一密码
    
    print("=" * 60)
    print("密码重置工具")
    print("=" * 60)
    print()
    print(f"将为所有账户设置统一密码:")
    print(f"  - 学生密码: {STUDENT_PASSWORD}")
    print(f"  - 教师密码: {TEACHER_PASSWORD}")
    print()
    
    confirm = input("确认要重置所有密码吗？(输入 yes 确认): ")
    if confirm.lower() != 'yes':
        print("已取消操作")
        return
    
    print()
    print("正在重置密码...")
    print()
    
    db = Database()
    try:
        # 重置学生密码
        student_hash = CryptoUtil.hash_password(STUDENT_PASSWORD)
        result = db.execute_query("SELECT student_id, name FROM students WHERE student_id != ''")
        
        success_count = 0
        for student in result:
            try:
                db.update_data(
                    'students',
                    {'password': student_hash},
                    {'student_id': student['student_id']}
                )
                print(f"  ✓ 学生: {student['student_id']} - {student['name']}")
                success_count += 1
            except Exception as e:
                print(f"  ✗ 失败: {student['student_id']} - {e}")
        
        print()
        print(f"✓ 已重置 {success_count} 个学生账户密码")
        print()
        
        # 重置教师密码
        teacher_hash = CryptoUtil.hash_password(TEACHER_PASSWORD)
        result = db.execute_query("SELECT teacher_id, name FROM teachers WHERE teacher_id != ''")
        
        success_count = 0
        for teacher in result:
            try:
                db.update_data(
                    'teachers',
                    {'password': teacher_hash},
                    {'teacher_id': teacher['teacher_id']}
                )
                print(f"  ✓ 教师: {teacher['teacher_id']} - {teacher['name']}")
                success_count += 1
            except Exception as e:
                print(f"  ✗ 失败: {teacher['teacher_id']} - {e}")
        
        print()
        print(f"✓ 已重置 {success_count} 个教师账户密码")
        print()
        
        print("=" * 60)
        print("✓ 密码重置完成！")
        print("=" * 60)
        print()
        print("登录信息:")
        print(f"  - 所有学生账户密码: {STUDENT_PASSWORD}")
        print(f"  - 所有教师账户密码: {TEACHER_PASSWORD}")
        print()
        print("示例登录:")
        print(f"  学号: 2021000001  密码: {STUDENT_PASSWORD}")
        print(f"  工号: teacher001   密码: {TEACHER_PASSWORD}")
        print()
        
    except Exception as e:
        Logger.error(f"重置密码失败: {e}", exc_info=True)
        print(f"\n✗ 操作失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_passwords()


"""
创建管理员账号的辅助脚本
如果管理员账号不存在，则创建默认管理员账号
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import Database
from utils.logger import Logger

def main():
    """创建管理员账号"""
    Logger.init()
    
    try:
        db = Database()
        
        # 调用确保管理员存在的方法
        db.ensure_admin_exists()
        
        # 验证管理员是否创建成功
        admin = db.execute_query("SELECT * FROM admins WHERE admin_id='admin001'")
        if admin:
            print("\n" + "=" * 60)
            print("✅ 管理员账号创建成功！")
            print("=" * 60)
            print(f"账号: admin001")
            print(f"密码: admin123")
            print(f"姓名: {admin[0]['name']}")
            print("=" * 60 + "\n")
        else:
            print("\n❌ 管理员账号创建失败，请检查日志\n")
            
    except Exception as e:
        Logger.error(f"创建管理员账号时出错: {e}", exc_info=True)
        print(f"\n❌ 错误: {e}\n")

if __name__ == "__main__":
    main()


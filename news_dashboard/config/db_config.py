from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import os
# Alwaysdata配置
# TiDB Cloud Serverless配置
ALWAYS_DATA_CONFIG = {
    'host': 'mysql-quicknews.alwaysdata.net',  # 替换为你的host
    'port': 3306,
    'user': 'quicknews',  # 替换为你的用户名
    'password': 'hbhhbh1010110',  # 替换为你的密码
    'database': 'quicknews_maindb',
}
def get_engine():
    """
    连接串格式：mysql+pymysql://user:password@host:port/database
    """
    # 【大作业连接串】截图以下这行进行分析：
    connection_string = (
        f"mysql+pymysql://{ALWAYS_DATA_CONFIG['user']}:{ALWAYS_DATA_CONFIG['password']}"
        f"@{ALWAYS_DATA_CONFIG['host']}:{ALWAYS_DATA_CONFIG['port']}"
        f"/{ALWAYS_DATA_CONFIG['database']}"
    )
    
    # 连接串各部分说明（用于报告）：
    # mysql+pymysql://  - 驱动类型（MySQL + PyMySQL适配器）
    # user:password@    - 身份认证信息
    # host:port          - 服务器地址和端口（Alwaysdata法国服务器）
    # /database          - 默认数据库名
    
    # 使用 connect_args 设置字符集和排序规则（解决存储过程collation冲突）
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=3,
        max_overflow=2,
        pool_pre_ping=True,
        pool_recycle=3600,  # Alwaysdata连接1小时回收
        connect_args={
            'charset': 'utf8mb4',
            'init_command': "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
        }
    )
    return engine

engine = get_engine()
def test_connection():
    """测试连接函数（用于main.py启动检查）"""
    try:
        conn = engine.connect()
        result = conn.execute(text("SELECT 'Alwaysdata Connected!', NOW(), DATABASE(), VERSION()"))
        row = result.fetchone()
        print(f"[DB Test] {row[0]}")
        print(f"[DB Test] 服务器时间: {row[1]}")
        print(f"[DB Test] 当前数据库: {row[2]}")
        print(f"[DB Test] MySQL版本: {row[3]}")
        conn.close()
        return True
    except Exception as e:
        print(f"[DB Test] 连接失败: {e}")
        return False
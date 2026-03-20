from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import os
# 获取当前文件所在目录（config文件夹）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录（config的上一级）
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
# 证书路径（根据实际文件名修改）
CA_CERT_PATH = os.path.join(PROJECT_ROOT, 'certs', 'tidb-ca.pem')  # 如果文件名是ca.pem
# TiDB Cloud Serverless配置
TIDB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',  # 替换为你的host
    'port': 4000,
    'user': '2fx6q5fYEfvHZPh.root',  # 替换为你的用户名
    'password': 'v80T5GMPPtNYpBSp',  # 替换为你的密码
    'database': 'test_connection',
}
def get_engine():
    """
    TiDB Cloud Serverless 专用连接配置
    关键：使用 connect_args 传递 SSL 参数，而不是连接字符串
    """
    connection_string = (
        f"mysql+pymysql://{TIDB_CONFIG['user']}:{TIDB_CONFIG['password']}"
        f"@{TIDB_CONFIG['host']}:{TIDB_CONFIG['port']}/{TIDB_CONFIG['database']}"
    )
    
    # 正确的 SSL 配置方式：通过 connect_args 传递字典
    connect_args = {
        'ssl_ca': CA_CERT_PATH,
        'ssl_verify_cert': True,
        'ssl_verify_identity': True
    }
    
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,  # 自动检测断线
        pool_recycle=1800,   # 30分钟回收（TiDB Serverless空闲连接会断）
        connect_args=connect_args  # 关键：SSL参数放这里
    )
    return engine

# 全局引擎实例
engine = get_engine()
def test_connection():
    """测试连接函数"""
    try:
        conn = engine.connect()
        # 关键修正：使用 text() 包装 SQL（SQLAlchemy 2.0 要求）
        result = conn.execute(text("SELECT 'TiDB Connected!', NOW(), DATABASE()"))
        row = result.fetchone()
        print(f"[DB Test] {row[0]}")
        print(f"[DB Test] 服务器时间: {row[1]}")
        print(f"[DB Test] 当前数据库: {row[2]}")
        conn.close()
        return True
    except Exception as e:
        print(f"[DB Test] 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False
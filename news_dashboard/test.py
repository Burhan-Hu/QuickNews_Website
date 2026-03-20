import pymysql
import ssl
import os


# 证书绝对路径（使用实际的文件名 tidb-ca.pem）
CA_CERT_PATH = r'D:\qknews\news_dashboard\certs\tidb-ca.pem'
# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 验证路径（调试用，确认后删除）
print(f"[DB Config] 证书路径: {CA_CERT_PATH}")
print(f"[DB Config] 证书存在: {os.path.exists(CA_CERT_PATH)}")
config = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',  # 替换为你的host
    'port': 4000,
    'user': '2fx6q5fYEfvHZPh.root',  # 替换为你的用户名
    'password': 'v80T5GMPPtNYpBSp',  # 替换为你的密码
    'database': 'test_connection',
    'connect_timeout': 10,
}
ca_path = os.path.join(CURRENT_DIR, 'certs', 'tidb-ca.pem')
# SSL配置
ssl_context = CA_CERT_PATH
print(f"证书路径: {ca_path}")
print(f"证书存在: {os.path.exists(ca_path)}")

try:
    print("正在连接TiDB...")
    
    # 正确方式1：使用 ssl_ca 参数（pymysql原生支持）
    conn = pymysql.connect(
        **config,
        ssl_ca=ca_path,  # 直接传证书路径字符串
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )
    
    # 或者正确方式2：使用 ssl 字典（如果上面的不行，试这个）
    # conn = pymysql.connect(
    #     **config,
    #     ssl={'ca': ca_path, 'verify_mode': 'CERT_REQUIRED'}
    # )
    
    print("✓ 连接成功！")
    
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello TiDB!', NOW(), DATABASE()")
    result = cursor.fetchone()
    print(f"服务器响应: {result[0]}")
    print(f"服务器时间: {result[1]}")
    print(f"当前数据库: {result[2]}")
    
    # 检查表是否存在
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"数据库中的表: {[t[0] for t in tables]}")
    
    conn.close()
    print("✓ 测试完成，连接正常！")
    
except Exception as e:
    print(f"✗ 连接失败: {e}")
    import traceback
    traceback.print_exc()  # 打印详细错误堆栈
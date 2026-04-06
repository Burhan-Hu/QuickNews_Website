#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移工具：从 Alwaysdata 迁移到 ClawCloud MySQL
"""
import os
import sys
import subprocess
import time

def run_command(cmd, description):
    """运行命令并打印输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ 成功")
        if result.stdout:
            print(result.stdout[:500])  # 只显示前500字符
    else:
        print(f"❌ 失败")
        print(f"错误: {result.stderr}")
    return result.returncode == 0

def migrate():
    """执行数据迁移"""
    
    # 配置
    ALWAYS_DATA_HOST = "mysql-quicknews.alwaysdata.net"
    ALWAYS_DATA_USER = "quicknews"
    ALWAYS_DATA_DB = "quicknews_maindb"
    
    # 从环境变量或输入获取密码
    always_data_password = os.environ.get('ALWAYS_DATA_PASSWORD') or input("请输入 Alwaysdata 数据库密码: ")
    
    NEW_MYSQL_HOST = os.environ.get('NEW_MYSQL_HOST') or input("请输入新 MySQL 地址 (默认: localhost): ") or "localhost"
    NEW_MYSQL_USER = os.environ.get('NEW_MYSQL_USER') or "root"
    NEW_MYSQL_PASSWORD = os.environ.get('NEW_MYSQL_PASSWORD') or input("请输入新 MySQL root 密码: ")
    NEW_MYSQL_DB = "quicknews_maindb"
    
    BACKUP_FILE = "db_backup.sql"
    
    print("\n" + "="*60)
    print("数据库迁移工具")
    print("从 Alwaysdata -> ClawCloud MySQL")
    print("="*60)
    
    # 步骤1: 从 Alwaysdata 导出数据
    print("\n步骤1: 导出 Alwaysdata 数据...")
    dump_cmd = (
        f'mysqldump -h {ALWAYS_DATA_HOST} -u {ALWAYS_DATA_USER} -p"{always_data_password}" '
        f'--routines --triggers --single-transaction '
        f'{ALWAYS_DATA_DB} > {BACKUP_FILE}'
    )
    
    if not run_command(dump_cmd, "导出数据"):
        print("导出失败，请检查密码和网络连接")
        return False
    
    # 检查备份文件大小
    if os.path.exists(BACKUP_FILE):
        size = os.path.getsize(BACKUP_FILE)
        print(f"✅ 备份文件大小: {size / 1024 / 1024:.2f} MB")
    else:
        print("❌ 备份文件未生成")
        return False
    
    # 步骤2: 等待新 MySQL 启动（如果是本地）
    if NEW_MYSQL_HOST in ['localhost', '127.0.0.1', 'mysql']:
        print("\n步骤2: 等待 MySQL 启动...")
        for i in range(30):
            test_cmd = f'mysql -h {NEW_MYSQL_HOST} -u {NEW_MYSQL_USER} -p"{NEW_MYSQL_PASSWORD}" -e "SELECT 1"'
            result = subprocess.run(test_cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                print("✅ MySQL 已启动")
                break
            print(f"等待 MySQL 启动... {i+1}s")
            time.sleep(1)
        else:
            print("❌ MySQL 启动超时")
            return False
    
    # 步骤3: 创建数据库（如果不存在）
    print("\n步骤3: 创建数据库...")
    create_db_cmd = (
        f'mysql -h {NEW_MYSQL_HOST} -u {NEW_MYSQL_USER} -p"{NEW_MYSQL_PASSWORD}" '
        f'-e "CREATE DATABASE IF NOT EXISTS {NEW_MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"'
    )
    run_command(create_db_cmd, "创建数据库")
    
    # 步骤4: 导入数据到新 MySQL
    print("\n步骤4: 导入数据到新 MySQL...")
    import_cmd = (
        f'mysql -h {NEW_MYSQL_HOST} -u {NEW_MYSQL_USER} -p"{NEW_MYSQL_PASSWORD}" '
        f'{NEW_MYSQL_DB} < {BACKUP_FILE}'
    )
    
    if not run_command(import_cmd, "导入数据"):
        print("导入失败")
        return False
    
    # 步骤5: 验证数据
    print("\n步骤5: 验证数据...")
    verify_cmd = (
        f'mysql -h {NEW_MYSQL_HOST} -u {NEW_MYSQL_USER} -p"{NEW_MYSQL_PASSWORD}" '
        f'{NEW_MYSQL_DB} -e "SELECT COUNT(*) as news_count FROM news;"'
    )
    run_command(verify_cmd, "验证新闻表数据")
    
    # 检查 Event Scheduler
    print("\n步骤6: 检查 Event Scheduler...")
    event_cmd = (
        f'mysql -h {NEW_MYSQL_HOST} -u {NEW_MYSQL_USER} -p"{NEW_MYSQL_PASSWORD}" '
        f'-e "SELECT @@event_scheduler;"'
    )
    run_command(event_cmd, "检查 Event Scheduler 状态")
    
    print("\n" + "="*60)
    print("✅ 数据迁移完成！")
    print("="*60)
    print(f"备份文件: {BACKUP_FILE}")
    print("请检查数据完整性后，再删除备份文件")
    
    return True

if __name__ == '__main__':
    try:
        success = migrate()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)

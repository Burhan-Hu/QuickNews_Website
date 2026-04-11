#!/usr/bin/env python3
"""
验证48小时清理机制是否正常工作
"""
import sys
sys.path.insert(0, 'd:\\qknews\\news_dashboard')

from config.db_config import engine
from sqlalchemy import text
from datetime import datetime

def check_cleanup():
    print("=" * 60)
    print("验证48小时清理机制")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 1. 检查Event Scheduler状态
        result = conn.execute(text("SHOW VARIABLES LIKE 'event_scheduler'"))
        row = result.fetchone()
        print(f"\n[1] Event Scheduler: {row[1] if row else 'Unknown'}")
        
        # 2. 查看最老新闻的时间
        result = conn.execute(text("""
            SELECT 
                MIN(created_at) as earliest,
                MAX(created_at) as latest,
                COUNT(*) as total,
                TIMESTAMPDIFF(HOUR, MIN(created_at), NOW()) as oldest_hours
            FROM news
        """))
        row = result.fetchone()
        print(f"\n[2] 新闻时间范围:")
        print(f"    最早: {row[0]} ({row[3]}小时前)")
        print(f"    最新: {row[1]}")
        print(f"    总数: {row[2]}条")
        
        if row[3] > 50:
            print(f"    ⚠️ 警告: 最老新闻超过48小时，清理可能未生效!")
        else:
            print(f"    ✅ 正常: 最老新闻在48小时内")
        
        # 3. 查看超过48小时的新闻数量
        result = conn.execute(text("""
            SELECT COUNT(*) as old_count
            FROM news
            WHERE created_at < DATE_SUB(NOW(), INTERVAL 48 HOUR)
        """))
        old_count = result.fetchone()[0]
        print(f"\n[3] 超过48小时的新闻: {old_count}条")
        if old_count == 0:
            print(f"    ✅ 清理正常，无过期新闻")
        else:
            print(f"    ⚠️ 有 {old_count} 条过期新闻未清理")
        
        # 4. 查看即将被清理的新闻（未来几小时）
        result = conn.execute(text("""
            SELECT COUNT(*) as will_delete
            FROM news
            WHERE created_at < DATE_SUB(NOW(), INTERVAL 46 HOUR)
            AND created_at >= DATE_SUB(NOW(), INTERVAL 48 HOUR)
        """))
        will_delete = result.fetchone()[0]
        print(f"\n[4] 即将被清理的新闻(46-48小时): {will_delete}条")
        
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)

if __name__ == '__main__':
    check_cleanup()

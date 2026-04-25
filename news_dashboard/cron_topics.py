# -*- coding: utf-8 -*-
"""
热点话题更新定时任务 - 供 Render Cron Job 使用
每小时执行一次热点话题聚类
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ir.xml_api import update_hot_topics_internal


def main():
    print("[Cron] 开始更新热点话题...")
    count = update_hot_topics_internal()
    print(f"[Cron] 热点话题更新完成，共 {count} 个话题")


if __name__ == "__main__":
    main()

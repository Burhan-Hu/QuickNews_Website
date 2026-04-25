# -*- coding: utf-8 -*-
"""
爬虫定时任务 - 供 Render Cron Job 使用
每 20 分钟执行一次新闻抓取
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler.jobs import NewsScheduler


def main():
    print("[Cron] 开始执行新闻抓取任务...")
    scheduler = NewsScheduler()
    scheduler.job_fetch_and_save()
    print("[Cron] 新闻抓取任务完成")


if __name__ == "__main__":
    main()

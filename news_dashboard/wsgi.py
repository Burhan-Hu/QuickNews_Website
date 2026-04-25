# -*- coding: utf-8 -*-
"""
WSGI 入口文件 - 供 Render Web Service 使用
用法: gunicorn --bind 0.0.0.0:$PORT wsgi:app
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ir.xml_api import app

if __name__ == "__main__":
    app.run()

#!/bin/bash
# 启动亚马逊财务管理系统
echo "启动财务管理系统..."
cd "$(dirname "$0")"
uv run streamlit run finance/app.py --server.port 8502

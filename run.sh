#!/bin/bash

cd "$(dirname "$0")"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "错误" message "未找到 Python3，请先安装 Python 3.8+"'
    exit 1
fi

# 安装依赖
python3 -m pip install -q requests beautifulsoup4 Pillow 2>/dev/null

# 运行程序
python3 main.py

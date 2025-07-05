#!/bin/bash

# 定时诊断脚本
# 使用方法: chmod +x 定时诊断.sh && ./定时诊断.sh

echo "开始执行数据源诊断..."
cd "$(dirname "$0")"
python3 数据源故障诊断.py

echo "诊断完成，时间: $(date)" 
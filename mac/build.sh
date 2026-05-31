#!/bin/bash
# Mac 构建脚本
# 需要先安装: pip3 install pyinstaller
pip3 install pyinstaller 2>/dev/null
pyinstaller --onefile --noconsole --name "CC-Status" --distpath "." claude_status.py
rm -rf build CC-Status.spec
echo "构建完成: ./CC-Status"

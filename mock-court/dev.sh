#!/bin/bash

echo "[1/2] Starting Frontend (Vite)..."
# 使用 npx vite 确保调用本地安装的 vite
npx vite & 

echo "[2/2] Opening Browser..."
# 给 Vite 一点启动时间
sleep 2

# 使用 WSL 专用的绝对路径调用 Windows 资源管理器
/mnt/c/Windows/explorer.exe "http://localhost:5173"

# 保持脚本运行，这样你按 Ctrl+C 就能停止 Vite
wait
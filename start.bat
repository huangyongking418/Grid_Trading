@echo off
chcp 65001 >nul
title 网格交易系统

:: 仅清理本项目上次启动的服务窗口
taskkill /f /fi "WINDOWTITLE eq GTS-Backend*" 2>nul
taskkill /f /fi "WINDOWTITLE eq GTS-Frontend*" 2>nul

timeout /t 2 /nobreak >nul

echo ========================================
echo   网格交易系统 - 启动中...
echo ========================================
echo.

echo [1/2] 启动后端 API 服务...
start "GTS-Backend" python "%~dp0backend\start_backend.py"
echo   后端启动中... (http://localhost:8000)

timeout /t 4 /nobreak >nul

echo [2/2] 启动前端页面服务...
start "GTS-Frontend" python "%~dp0frontend\start_frontend.py"
echo   前端启动中... (http://localhost:5173)

echo.
echo ========================================
echo   系统启动完成！
echo.
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo ========================================
echo.
echo 按任意键关闭本窗口（服务继续运行）
pause >nul

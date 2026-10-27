@echo off
chcp 65001 >nul
title 网格交易系统 - 停止

echo ========================================
echo   正在停止网格交易系统...
echo ========================================
echo.

:: 方式1: 窗口标题
taskkill /f /fi "WINDOWTITLE eq GTS-Frontend*" 2>nul
echo [前端] 已停止

taskkill /f /fi "WINDOWTITLE eq GTS-Backend*" 2>nul

:: 方式2: 停止本项目的后端服务窗口
taskkill /f /fi "WINDOWTITLE eq GTS-Backend*" 2>nul
echo [后端] 已停止

:: 方式3: 停止本项目的前端服务窗口
taskkill /f /fi "WINDOWTITLE eq GTS-Frontend*" 2>nul
echo [前端] 已停止

echo.
echo 所有服务已停止。
echo 可以安全关闭此窗口。
pause >nul

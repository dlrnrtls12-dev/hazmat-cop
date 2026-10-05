@echo off
chcp 65001 > nul
title Hazmat Cop - 위험물 기획단속 스마트 현장도우미
cd /d "c:\Users\이국신\Desktop\hazmat cop"

echo ========================================================
echo   Hazmat Cop - 위험물 기획단속 스마트 현장도우미 가동
echo ========================================================
echo.
echo [1] 가상환경 활성화 및 서버 시작 중...
echo [2] 브라우저가 잠시 후 자동으로 열립니다 (http://127.0.0.1:8000)
echo.

start "" http://127.0.0.1:8000
.\.venv\Scripts\python app.py
pause

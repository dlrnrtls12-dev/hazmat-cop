@echo off
chcp 65001 > nul
title 소방특사경 위험물 단속도우미 (HAZMAT COP)
cls

echo ======================================================================
echo   소방특별사법경찰 위험물 기획단속 스마트 현장도우미 [HAZMAT COP]
echo ======================================================================
echo.

cd /d "%~dp0"

:: 포트 8000 사용 여부 확인
netstat -ano | findstr :8000 > nul
if %ERRORLEVEL% equ 0 (
    echo [안내] 서버가 이미 백그라운드에서 정상 작동 중입니다!
    echo [안내] 웹 브라우저를 바로 엽니다: http://localhost:8000
    start "" http://localhost:8000
    timeout /t 3 > nul
    exit /b 0
)

echo [1/2] 로컬 단속 엔진을 실행하는 중입니다...
echo (이 창을 닫으면 서버가 종료되므로 최소화하여 켜두세요)
echo.

if exist "cloudflared.exe" (
    echo [안내] 외부 모바일(LTE/5G) 전용 보안 터널을 연결 중입니다...
    start /B .\cloudflared.exe tunnel --url http://localhost:8000 > nul 2>&1
)

start "" http://localhost:8000
.\.venv\Scripts\python app.py

pause

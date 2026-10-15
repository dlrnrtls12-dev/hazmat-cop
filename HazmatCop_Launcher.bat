@echo off
chcp 65001 > nul
title 소방특사경 위험물 단속도우미 (HAZMAT COP)
cls
echo ========================================================
echo   소방특별사법경찰 위험물 기획단속 스마트 현장도우미
echo   HAZMAT ENFORCER 원클릭 자동 실행기
echo ========================================================
echo.
echo [1/2] 로컬 인공지능 단속 엔진을 기동 중입니다...
cd /d "%~dp0"
start /B .\.venv\Scripts\uvicorn app:app --host 0.0.0.0 --port 8000 > nul 2>&1

timeout /t 2 > nul
echo [2/2] 웹 브라우저를 자동으로 실행합니다...
start http://localhost:8000

echo.
echo ========================================================
echo   프로그램이 정상적으로 실행되었습니다!
echo   - PC 접속: http://localhost:8000
echo   - 스마트폰 접속: 상단 메뉴의 [모바일 연결 QR코드] 스캔
echo ========================================================
echo   (이 창을 닫으셔도 백그라운드에서 계속 실행됩니다)
pause

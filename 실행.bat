@echo off
chcp 65001 > nul
echo.
echo ====================================
echo  인간행동과 사회환경 Q^&A 챗봇 실행
echo ====================================
echo.

:: Flask 서버 실행
echo [1/2] 챗봇 서버 시작 중...
start /B python "%~dp0app.py"
timeout /t 8 /nobreak > nul

:: ngrok 고정 도메인으로 터널 실행
echo [2/2] 외부 접속 터널 시작 중...
start /B "%~dp0ngrok.exe" http 5000 --domain=nonenigmatic-shonta-distressedly.ngrok-free.dev
timeout /t 5 /nobreak > nul

echo.
echo ✅ 챗봇이 실행되었습니다!
echo.
echo  로컬 접속: http://localhost:5000
echo  외부 접속: https://nonenigmatic-shonta-distressedly.ngrok-free.dev
echo.
echo 이 창을 닫으면 챗봇이 종료됩니다.
echo.
pause

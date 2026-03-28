@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cd /d %~dp0

echo [1/2] 가상환경 활성화 및 PyInstaller 설치 확인...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
pip install pyinstaller

echo [2/2] EXE 파일 빌드 중 (콘솔창 숨김 옵션 적용)...
pyinstaller --noconfirm --onefile --windowed --name "ZaiQuotaMonitor" query_quota.py

echo.
echo 빌드 최적화 (불필요한 파일 정리 중)...
copy /Y "dist\ZaiQuotaMonitor.exe" "ZaiQuotaMonitor.exe" > nul
rmdir /S /Q build
rmdir /S /Q dist
del /Q ZaiQuotaMonitor.spec

echo.
echo 빌드가 완료되었습니다! 
echo 메인 폴더에 ZaiQuotaMonitor.exe 파일이 생성되었습니다.
pause
endlocal

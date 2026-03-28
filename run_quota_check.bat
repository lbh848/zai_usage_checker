@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cd /d %~dp0

echo 시작: %date% %time%

:: config.py 파일 존재 확인
if not exist "config.py" (
    echo [오류] config.py 파일이 없습니다!
    pause
    exit /b 1
)

:: Check if venv exists
if not exist "venv" (
    echo [1/3] Creating virtual environment ^(venv^)...
    python -m venv venv
    if errorlevel 1 (
        echo [오류] venv 생성 실패! Python 설치 확인하세요.
        pause
        exit /b 1
    )
)

:: Activate venv and install requirements
echo [2/3] Activating venv and installing requirements...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [오류] venv 활성화 실패!
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [경고] requirements.txt 설치 중 일부 실패. 계속 진행...
)

:: Check if config.py has placeholders or if external key exists
set "USE_EXTERNAL_KEY=0"
if exist "%USERPROFILE%\.local\share\opencode\auth.json" (
    set "USE_EXTERNAL_KEY=1"
)
if exist "key\zai.key" (
    set "USE_EXTERNAL_KEY=1"
)

if !USE_EXTERNAL_KEY! == 0 (
    findstr /C:"YOUR_API_KEY_HERE" config.py >nul 2>nul
    if !errorlevel! == 0 (
        echo.
        echo [WARN] ~/.local/share/opencode/auth.json 파일에 관련 API 키를 설정하거나, 
        echo        key/zai.key 파일에 API 키를 입력해주세요!
        echo.
        pause
        exit /b 1
    )
)
echo [확인] API 키 설정 확인됨.

:: Run the quota query script
echo [3/3] Querying Zhipu AI / Z.ai Quota...
python query_quota.py
if errorlevel 1 (
    echo [경고] query_quota.py 실행 중 오류 발생.
)

echo 완료: %date% %time%
pause
endlocal
@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cd /d %~dp0

echo 시작: %date% %time%

:: Check key file
if not exist "key\zai.key" (
    echo [오류] key/zai.key 파일이 없습니다! key 폴더를 만들고 zai.key 파일 안에 API 키를 넣어주세요.
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

:: Run the quota query script
echo [3/3] Querying Zhipu AI / Z.ai Quota...
python query_quota.py
if errorlevel 1 (
    echo [경고] query_quota.py 실행 중 오류 발생.
)

echo 완료: %date% %time%
pause
endlocal
# Zhipu AI & Z.ai Quota Checker

Zhipu AI 및 Z.ai의 5시간 토큰 사용 한도 및 MCP 월별 할당량을 실시간으로 조회하는 간단한 스크립트 도구입니다.

## 파일 구성
* `config.py` : API 키를 설정하는 파일입니다.
* `query_quota.py` : 할당량을 조회하는 메인 파이썬 스크립트.
* `run_quota_check.bat` : 클릭 한 번으로 가상환경 구축, 패키지 설치 및 조회를 실행하는 배치 파일.

## 사용 방법

1. **API 키 설정**
   `config.py` 파일을 열고 본인의 Zhipu AI 또는 Z.ai API 키를 입력합니다.

2. **할당량 확인 실행**
   `run_quota_check.bat` 파일을 더블 클릭하여 실행합니다. 
   - 처음 실행 시 자동으로 Python 가상환경을 생성하고 필요한 패키지(`requirements.txt`)를 설치합니다. 
   - 설치 완료 후 실시간으로 현재 계정의 토큰 사용량과 남은 한도, MCP 할당량 등을 콘솔창에 출력합니다.

## 요구 사항
* Python 3.x 가 설치되어 있어야 하며 환경변수 경로에 설정되어 있어야 합니다.

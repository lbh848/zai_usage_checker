# Z.ai Quota Monitor

## 프로젝트 개요

Z.ai의 사용량 할당량을 실시간으로 조회하는 GUI 모니터링 도구입니다.

## 검색 도구

웹 검색이 필요한 경우 **search-engine MCP 서버의 도구**를 사용하세요.
- `tavily_search(query)` — 웹 검색
- `tavily_extract(urls)` — URL 콘텐츠 추출
- `tavily_crawl(url)` — 사이트 크롤링

내장 WebSearch 도구 대신 위 도구를 우선적으로 사용합니다.

## 파일 구조

- `query_quota.py` — 메인 스크립트 (할당량 조회 + tkinter GUI)
- `config.py` — API 키 로드 (auth.json → key/zai.key 순서)
- `key/zai.key` — API 키 파일
- `run_quota_check.bat` — 실행 스크립트 (가상환경 자동 구성)
- `build_exe.bat` — PyInstaller EXE 빌드 스크립트

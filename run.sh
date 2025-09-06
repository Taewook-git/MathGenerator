#!/bin/bash

# 환경 변수 초기화 (시스템 환경 변수 무시)
unset GEMINI_API_KEY

# .env 파일에서만 로드
export $(cat .env | grep -v '^#' | xargs)

# Streamlit 실행
streamlit run src/ui/app.py
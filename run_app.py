#!/usr/bin/env python3
"""
KSAT Math AI 실행 스크립트
"""

import streamlit.web.cli as stcli
import sys
import os

if __name__ == '__main__':
    # Streamlit 앱 실행
    sys.argv = ["streamlit", "run", "src/ui/app.py", 
                "--server.port", "8501",
                "--server.headless", "false"]
    sys.exit(stcli.main())
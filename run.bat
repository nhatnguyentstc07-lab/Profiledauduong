@echo off
REM Khởi động hệ thống luyện phản biện AI
cd /d "%~dp0"
python -m streamlit run app.py

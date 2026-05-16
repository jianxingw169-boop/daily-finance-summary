@echo off
cd /d "C:\Users\王建行\daily-finance-summary"
set LOG_FILE="daily-finance.log"
echo [%date% %time%] 启动每日金融推送 >> %LOG_FILE%
"C:\Users\王建行\AppData\Local\Python\pythoncore-3.14-64\python.exe" main.py --schedule >> %LOG_FILE% 2>&1

@echo off
chcp 65001 >nul
cd /d C:\AIDEOM_VN\AIDEOM_VN_Final

echo [1/5] Cai hoac cap nhat google-genai...
python -m pip install -U google-genai
if errorlevel 1 goto :error

echo [2/5] Them google-genai vao requirements.txt...
findstr /I /C:"google-genai" requirements.txt >nul
if errorlevel 1 echo google-genai>>requirements.txt

echo [3/5] Xoa cache Python...
if exist services\__pycache__ rmdir /S /Q services\__pycache__
if exist ui\__pycache__ rmdir /S /Q ui\__pycache__
if exist pages\__pycache__ rmdir /S /Q pages\__pycache__

echo [4/5] Kiem tra cu phap...
python -m compileall -q services ui pages
if errorlevel 1 goto :error

echo [5/5] Hoan tat.
echo.
echo Hay chay:
echo python -m streamlit run app.py
echo.
pause
exit /b 0

:error
echo.
echo CAP NHAT KHONG THANH CONG. Xem loi o phia tren.
pause
exit /b 1

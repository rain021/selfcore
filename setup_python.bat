@echo off
echo ============================================
echo   SelfCore - Python Dependencies Setup
echo ============================================
echo.
echo Installing Python packages...
py -3 -m pip install -r requirements.txt
echo.
echo Downloading spaCy English model...
py -3 -m spacy download en_core_web_sm
echo.
echo Downloading spaCy Korean model...
py -3 -m spacy download ko_core_news_sm
echo.
echo ============================================
echo   Done! You can now launch SelfCore.
echo ============================================
pause

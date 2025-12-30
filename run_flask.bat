@echo off
REM Check if the virtual environment folder exists
IF NOT EXIST "venv" (
    echo Virtual environment not found. Creating one...
    REM Create the virtual environment
    python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Install dependencies from requirements.txt (if not already installed)
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables for Flask
set FLASK_APP=app.py
set FLASK_ENV=development

REM Run the Flask app to listen on all network interfaces
python app.py

REM Pause to keep the window open
pause



@echo off
REM Setup script for Inventory Management System (Windows)

echo.
echo ============================================
echo Inventory Management System Setup
echo ============================================
echo.

REM 1. Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM 2. Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 3. Create .env file if it doesn't exist
if not exist .env (
    echo.
    echo Creating .env file...
    (
        echo SECRET_KEY=your-secret-key-here
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
    ) > .env
)

REM 4. Run migrations
echo.
echo Running migrations...
python manage.py migrate

REM 5. Load fixture data
echo.
echo Loading database from fixtures...
python manage.py loaddata fixtures/db_data.json

REM 6. Collect static files (optional)
REM python manage.py collectstatic --noinput

echo.
echo ============================================
echo Setup complete!
echo ============================================
echo.
echo To start the server:
echo   python manage.py runserver
echo.
echo To create a superuser:
echo   python manage.py createsuperuser
echo.
pause

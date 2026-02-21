# Setup Guide for Inventory Management System

## Quick Start

### Windows
```bash
setup.bat
```

### macOS/Linux
```bash
bash setup.sh
```

## What the setup does:
1. ✅ Creates Python virtual environment
2. ✅ Installs all dependencies from `requirements.txt`
3. ✅ Sets up `.env` configuration file
4. ✅ Runs Django migrations
5. ✅ Loads all database data from fixtures
6. ✅ Ready to run!

## Starting the Server
```bash
python manage.py runserver
```

Then visit: http://localhost:8000

## Creating a Superuser (Admin Account)
```bash
python manage.py createsuperuser
```

## Database Data
- Current database data is stored in: `fixtures/db_data.json`
- **Do NOT commit** `db.sqlite3` - it's in `.gitignore`
- The fixture file contains all your current data and will be loaded automatically during setup

## File Structure
```
.
├── setup.sh              # Setup script for Linux/macOS
├── setup.bat             # Setup script for Windows
├── requirements.txt      # Python dependencies
├── manage.py             # Django management script
├── db.sqlite3            # (LOCAL ONLY - not in git)
├── fixtures/
│   └── db_data.json      # Your database data (committed to git)
└── ...
```

## Updating the Fixture
If you make changes to the database and want to save them:
```bash
python manage.py dumpdata --indent 2 > fixtures/db_data.json
```

Then commit and push:
```bash
git add fixtures/db_data.json
git commit -m "Update database fixture with new data"
git push
```

## Troubleshooting

### Issue: "No such file or directory: 'fixtures/db_data.json'"
**Solution:** Make sure you're in the project root directory and the fixtures folder exists.

### Issue: "django.db.utils.ProgrammingError"
**Solution:** Run migrations first:
```bash
python manage.py migrate
```

### Issue: Virtual environment not activating
**Windows:**
```bash
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

#!/bin/bash
# Setup script for Inventory Management System

echo "🚀 Setting up Inventory Management System..."

# 1. Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    echo "SECRET_KEY=your-secret-key-here" > .env
    echo "DEBUG=True" >> .env
    echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> .env
fi

# 4. Run migrations
echo "🗄️ Running migrations..."
python manage.py migrate

# 5. Load fixture data
echo "📊 Loading database from fixtures..."
python manage.py loaddata fixtures/db_data.json

# 6. Collect static files (optional)
# python manage.py collectstatic --noinput

echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  python manage.py runserver"
echo ""
echo "To create a superuser:"
echo "  python manage.py createsuperuser"

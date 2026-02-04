# Quran Django Project

## Project Setup

Follow these steps to set up and run the Django project.

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database Settings

Update the database settings in `settings.py` if needed (default is SQLite):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

For PostgreSQL, MySQL, or other databases, update accordingly and ensure the database service is running.

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)

Create an admin user to access the Django admin interface:

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 7. Populate Quran Data

Run the custom management command to populate the database with Quran data:

```bash
python manage.py download_quran_data
python manage.py download_bn_trans
```

**Note:** This command may take a few moments to complete as it loads all Quranic data into the database.

### 8. Run Development Server

```bash
python manage.py runserver
```

Access the application at:
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Common Commands

### Development
```bash
python manage.py runserver  # Start development server
python manage.py runserver 8080  # Run on specific port
```

### Database Operations
```bash
python manage.py makemigrations  # Create new migrations
python manage.py migrate  # Apply migrations
python manage.py migrate --plan  # Show migration plan without applying
python manage.py showmigrations  # List all migrations and their status
```

### Admin
```bash
python manage.py createsuperuser  # Create admin user
python manage.py changepassword <username>  # Change user password
```

## Troubleshooting

### 1. Port Already in Use
If port 8000 is occupied:
```bash
python manage.py runserver 8001
```

### 2. Migration Errors
If you encounter migration issues:
```bash
python manage.py migrate --fake
python manage.py migrate --run-syncdb
```

### 3. Missing Dependencies
If `pip install` fails:
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 4. Database Issues
For SQLite lock issues, ensure no other process is using the database file.

## Environment Variables (Optional)

For production, consider using environment variables in `settings.py`:

```python
import os

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-secret-key-here')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
```

## Production Deployment

For production deployment, additional steps are required:

1. Set `DEBUG = False` in `settings.py`
2. Configure a production database (PostgreSQL recommended)
3. Set up a web server (Nginx/Apache) with WSGI (Gunicorn/uWSGI)
4. Configure static files collection: `python manage.py collectstatic`
5. Set up proper security measures and HTTPS

## Support

For issues or questions, please check:
- Django documentation: https://docs.djangoproject.com/
- Project issue tracker (if available)
- Python virtual environment guide: https://docs.python.org/3/library/venv.html
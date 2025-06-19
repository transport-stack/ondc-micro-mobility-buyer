# delete all migration files
find . -path "*/migrations/*.py" -not -name "__init__.py" -not -path "./venv/*" -not -path "./env/*" -delete
find . -path "*/migrations/*.pyc" -not -path "./venv/*" -not -path "./env/*" -delete

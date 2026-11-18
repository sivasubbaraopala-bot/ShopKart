
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate

python manage.py shell -c "import os; from django.contrib.auth import get_user_model; U=get_user_model(); u,created=U.objects.get_or_create(username='siva'); u.is_staff=True; u.is_superuser=True; u.set_password(os.environ['DJANGO_ADMIN_PASSWORD']); u.save(); print('Admin account siva ready')"

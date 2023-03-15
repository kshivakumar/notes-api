#!/bin/bash
set -e

PYTHON=python3.8
PIP=pip3.8

yum update -y
yum install git -y
amazon-linux-extras install $PYTHON -y # later versions are not available in amazon-linux-extras

mkdir /app
cd /app

git clone https://github.com/kshivakumar/notes-api .

$PIP install -r requirements.txt

cat <<EOF > /app/.env
DJANGO_DEBUG=${django_debug}
DJANGO_SECRET_KEY="${django_secret_key}"
DJANGO_DB_HOST="${postgres_host}"
DJANGO_DB_NAME="${postgres_dbname}"
DJANGO_DB_USERNAME="${postgres_username}"
DJANGO_DB_PASSWORD="${postgres_password}"
EOF

$PYTHON manage.py migrate

mkdir -p ${django_static_root}
chown ec2-user:ec2-user ${django_static_root}
chmod 755 ${django_static_root}
$PYTHON manage.py collectstatic --noinput

$PYTHON manage.py create_sample_data --skip-if-exists

cat <<EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn daemon
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/app
EnvironmentFile=/app/.env
ExecStart=/usr/local/bin/gunicorn --workers 3 --preload --bind 0.0.0.0:${gunicorn_port} wsgi:application
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start gunicorn


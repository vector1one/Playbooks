#!/bin/sh
set -e
python3 /var/www/localhost/cgi-bin/init_db.py
exec httpd -D FOREGROUND

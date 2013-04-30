# Moodload

Makes it possible to download all files from any course on Moodle in a click.

### nginx.conf

```nginx
user                    www-data;
worker_processes        4;
pid                     /var/run/nginx.pid;

events
{
    worker_connections  1024;
}

http
{
    access_log          /var/log/nginx/access.log;
    error_log           /var/log/nginx/error.log;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   4;

    gzip                on;
    gzip_comp_level     2;
    gzip_proxied        any;
    gzip_disable        "MSIE [1-6]\.(?!.*SV1)";

    include             /etc/nginx/mime.types;
    include             /etc/nginx/conf.d/*.conf;
    include             /etc/nginx/sites-enabled/*;
}
```

### sites-available/moodload

```nginx
server
{
    listen              80;
    listen              [::]:80 default ipv6only=on;
    server_name         moodload.jeremejevs.com;

    access_log          /var/log/nginx/moodload.access.log;
    error_log           /var/log/nginx/moodload.error.log;

    uwsgi_read_timeout  300;
    uwsgi_send_timeout  300;

    location = /
    {
        alias           /srv/moodload/;
        uwsgi_pass      127.0.0.1:8001;
        include         uwsgi_params;
    }

    location /
    {
        alias           /srv/moodload/static/;
    }
}
```

### bash

```bash
cd /srv/moodload
source /srv/.venvs/moodload/bin/activate
uwsgi --master --processes=4 --socket=:8001 --wsgi-file=moodload.py
```

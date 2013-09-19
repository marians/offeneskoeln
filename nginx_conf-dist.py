upstream offeneskoeln_gunicorn {
    server unix:/tmp/gunicorn-offeneskoeln.sock max_fails=3 fail_timeout=30s;
}

server {
    client_max_body_size 4G;

    server_name  dev.offeneskoeln.de;

    access_log  /var/log/nginx/offeneskoeln.de.access.log;
    error_log   /var/log/nginx/offeneskoeln.de.error.log;

    gzip             on;
    gzip_min_length  1000;
    gzip_types       text/plain text/css application/json application/javascript application/x-javascript;
    gzip_disable     "MSIE [1-6]\.";

    root   /home/ok/offeneskoeln/webapp;

    location /attachments {
        autoindex  on;
        add_header X-Robots-Tag "noarchive, noimageindex";
        expires    modified +90d;
    }

    location /static {
        expires    modified +30d;
    }

    location / {
            try_files $uri @proxy_to_app;
    }

    location @proxy_to_app {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://offeneskoeln_gunicorn;
    }

}
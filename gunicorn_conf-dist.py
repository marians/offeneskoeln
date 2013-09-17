workers = 3
bind = 'unix:/tmp/gunicorn-offeneskoeln.sock'
accesslog = '/var/log/gunicorn/offeneskoeln-webapp.access.log'
errorlog = '/var/log/gunicorn/offeneskoeln-webapp.error.log'
proc_name = 'offeneskoeln-webapp'
loglevel = 'info'

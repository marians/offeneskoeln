#!/bin/bash
# Bochum
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/export_attachments.py bochum 2013
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_data_dump.py bochum

#Moers
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/export_attachments.py moers 2013

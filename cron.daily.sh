#!/bin/bash
# Bochum
cd /opt/ris-scraper/
sudo -u ris-scraper /opt/ris-scraper/ris-scraper/bin/python /opt/ris-scraper/main.py -c bochum --start 2013-01 --end 2013-12
cd /opt/ris-web/
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_fulltext.py bochum
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_georeferences.py bochum
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_thumbs.py bochum
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_submissions_rss_feed.py bochum
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/elasticsearch_import.py bochum


# Moers
cd /opt/ris-scraper/
sudo -u ris-scraper /opt/ris-scraper/ris-scraper/bin/python /opt/ris-scraper/main.py -c moers --start 2013-01 --end 2013-12
cd /opt/ris-web/
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_fulltext.py moers
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_georeferences.py moers
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_thumbs.py moers
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_submissions_rss_feed.py moers
sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/elasticsearch_import.py moers

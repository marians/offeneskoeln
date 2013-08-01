#!/bin/bash
#Config
CITIES=('bochum' 'moers' 'duisburg')

#CDN
umount /srv/www/static/
mount /srv/www/static/

for CITY in "${CITIES[@]}"
do
  cd /opt/ris-scraper/
  sudo -u ris-scraper /opt/ris-scraper/ris-scraper/bin/python /opt/ris-scraper/main.py -c $CITY --start 2013-06 --end 2013-12
  cd /opt/ris-web/
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_fulltext.py $CITY
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_georeferences.py $CITY
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_thumbs.py $CITY
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_submissions_rss_feed.py $CITY
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/elasticsearch_import.py $CITY
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/generate_data_dump.py $CITY
  sudo -u ris-web /opt/ris-web/ris-web/bin/python /opt/ris-web/scripts/export_attachments.py $CITY
done

#CDN
umount /srv/www/static/
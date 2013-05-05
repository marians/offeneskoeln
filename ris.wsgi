activate_this = '/opt/ris-web/ris-web/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import os
os.environ['CITY_CONF']='/opt/ris-web/city/bochum.py'

import sys
sys.path.insert(0, '/opt/ris-web')
from webapp import app as application

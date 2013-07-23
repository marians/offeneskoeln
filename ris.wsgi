activate_this = '/opt/ris-web/ris-web/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/opt/ris-web')
from webapp import app as application

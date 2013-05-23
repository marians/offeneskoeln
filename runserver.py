import os
os.environ['CITY_CONF']='/opt/ris-web/city/bochum.py'

from webapp import app

app.run(debug=True, host='0.0.0.0')

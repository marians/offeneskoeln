
# Makefile zur automatischen Erzeugung der OSM-Daten-Derivate

# Benötigt python-osm!
# pip install git+git://github.com/werner2101/python-osm.git
# das wiederum benötigt NumPy und Matplotlib.nxutils
# pip install numpy
# pip install matplotlib

# Aufruf mit Laden der Config: make `cat bochum.cfg`

import: city-streets.osm
	python osm-import.py city-streets.osm $(CITY)

city-streets.osm: osmfilter city.osm
	./osmfilter city.osm \
	--keep="highway=primary =secondary =tertiary =residential =unclassified =road =living-street =pedestrian" \
	--drop-author --drop-version > city-streets.osm

city.osm: city.poly city-regbez-latest.osm osmosis
	bin/osmosis --read-xml file="city-regbez-latest.osm" --bounding-polygon file="city.poly" --write-xml file="city.osm"

city-regbez-latest.osm:
	wget -N http://download.geofabrik.de/europe/germany/$(FOLDER)$(FILE)-latest.osm.bz2
	bunzip2 $(FILE)-latest.osm.bz2
	mv $(FILE)-latest.osm city-regbez-latest.osm

osmfilter: loadconf
	wget -O - http://m.m.i24.cc/osmfilter.c |cc -x c - -O3 -o osmfilter

loadconf:
	cat $(CITY).cfg

osmosis:
	wget -N http://bretth.dev.openstreetmap.org/osmosis-build/osmosis-latest.tgz
	tar xzf osmosis-latest.tgz
	chmod u+x bin/osmosis
	cp bin/osmosis .
	rm osmosis-latest.tgz
	rm -r script
	rm readme.txt
	rm copying.txt
	rm changes.txt

city.poly:
	python -m osm.multipolygon -r $(OSM_RELATION) -m city.poly

clean:
	rm -f city.poly
	rm -f *.osm
	rm -rf osmfilter
	rm -rf osmosis
	rm -rf bin
	rm -rf lib
	rm -rf config

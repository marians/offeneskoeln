
# Makefile zur automatischen Erzeugung der OSM-Daten-Derivate

# Benötigt python-osm!
# pip install git+git://github.com/werner2101/python-osm.git
# das wiederum benötigt NumPy und Matplotlib.nxutils
# pip install numpy
# pip install matplotlib

CITY=bochum
REGBEZ=arnsberg
OSM_RELATION=62644


import: city-streets.osm
	python osm-import.py city-streets.osm

city-streets.osm: osmfilter city.osm
	./osmfilter city.osm \
	--keep="highway=primary =secondary =tertiary =residential =unclassified =road =living-street =pedestrian" \
	--drop-author --drop-version > city-streets.osm

city.osm: city.poly city-regbez-latest.osm osmosis
	bin/osmosis --read-xml file="city-regbez-latest.osm" --bounding-polygon file="city.poly" --write-xml file="city.osm"

city-regbez-latest.osm:
	wget -N http://download.geofabrik.de/europe/germany/nordrhein-westfalen/$(REGBEZ)-regbez-latest.osm.bz2
	bunzip2 $(REGBEZ)-regbez-latest.osm.bz2
	mv $(REGBEZ)-regbez-latest.osm city-regbez-latest.osm

osmfilter:
	wget -O - http://m.m.i24.cc/osmfilter.c |cc -x c - -O3 -o osmfilter

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
	rm city.poly
	rm *.osm
	rm -r osmfilter
	rm -r osmosis
	rm -r bin
	rm -r lib
	rm -r config


# Makefile zur automatischen Erzeugung der OSM-Daten-Derivate

# Benötigt python-osm!
# pip install git+git://github.com/werner2101/python-osm.git
# das wiederum benötigt NumPy und Matplotlib.nxutils
# pip install numpy
# pip install matplotlib

import: koeln-streets.osm
	python osm-import.py

koeln-streets.osm: osmfilter koeln.osm
	./osmfilter koeln.osm \
	--keep="highway=primary =secondary =tertiary =residential =unclassified =road =living-street =pedestrian" \
	--drop-author --drop-version > koeln-streets.osm

koeln.osm: koeln.poly koeln-regbez-latest.osm osmosis
	bin/osmosis --read-xml file="koeln-regbez-latest.osm" --bounding-polygon file="koeln.poly" --write-xml file="koeln.osm"

koeln-regbez-latest.osm:
	wget -N http://download.geofabrik.de/europe/germany/nordrhein-westfalen/koeln-regbez-latest.osm.bz2
	bunzip2 koeln-regbez-latest.osm.bz2

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

koeln.poly:
	python -m osm.multipolygon -r 62578 -m koeln.poly

clean:
	rm koeln.poly
	rm koeln-regbez.osm.bz2
	rm koeln-regbez.osm
	rm koeln.osm
	rm osmfilter
	rm koeln-streets.osm
	rm -r osmosis_dir
	rm osmosis
	rm -r bin
	rm -e lib
	rm -r config

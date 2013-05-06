
# Makefile zur automatischen Erzeugung der OSM-Daten-Derivate

# Benötigt python-osm!
# pip install git+git://github.com/werner2101/python-osm.git
# das wiederum benötigt NumPy und Matplotlib.nxutils
# pip install numpy
# pip install matplotlib

CITY=bochum
REGBEZ=arnsberg


import: $(city)-streets.osm
	python osm-import.py bochum-streets.osm

bochum-streets.osm: osmfilter bochum.osm
	./osmfilter bochum.osm \
	--keep="highway=primary =secondary =tertiary =residential =unclassified =road =living-street =pedestrian" \
	--drop-author --drop-version > bochum-streets.osm

bochum.osm: bochum.poly arnsberg-regbez-latest.osm osmosis
	bin/osmosis --read-xml file="arnsberg-regbez-latest.osm" --bounding-polygon file="bochum.poly" --write-xml file="bochum.osm"

arnsberg-regbez-latest.osm:
	wget -N http://download.geofabrik.de/europe/germany/nordrhein-westfalen/arnsberg-regbez-latest.osm.bz2
	bunzip2 arnsberg-regbez-latest.osm.bz2

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

bochum.poly:
	python -m osm.multipolygon -r 62644 -m bochum.poly

clean:
	rm bochum.poly
	rm *.osm
	rm *.pyc
	rm -r osmfilter
	rm -r osmosis
	rm -r bin
	rm -r lib
	rm -r config

/**
 * offeneskoeln.de custom javascript
 * Author: Marian Steinbach
 */
var disqus_shortname = 'offeneskoeln';
var OffenesKoeln = {
    
    a: 6378137,
    b: (6378137 * 297.257223563) / 298.257223563,
    
    monthstr: {
            '01': 'Januar',
            '02': 'Februar',
            '03': 'März',
            '04': 'April',
            '05': 'Mai',
            '06': 'Juni',
            '07': 'Juli',
            '08': 'August',
            '09': 'September',
            '10': 'Oktober',
            '11': 'November',
            '12': 'Dezember'
        },
        
    /**
     * returns a list of streets for a given position
     * which are in a given rdius
     */
    streetsForPosition: function(lat, lon, radius, callback) {
        $.getJSON('/api/streets', {'lat': lat, 'lon': lon, 'radius': radius}, callback);
    },
    /**
     * returns a list of position coordinates for a street name,
     * as well as the average coordinates
     */
    locationsForStreet: function(name, list_nodes, callback) {
        var contain = ['result', 'average'];
        if (!list_nodes) {
            contain = ['average'];
        }
        $.getJSON('/api/locations', {'street': name, 'contain': contain.join(',')}, callback);
    },
    /**
     * Does the same as locationsForStreet, but for a list of names.
     * Requests are queued.
     */
    locationsForStreetsQueued: function(names, callback) {
        for (var name in names) {
            $.ajaxq('locationsForStreetsQueuedQueue', {
                url: "/api/locations",
                data: { street: names[name], output: 'averages'},
                dataType: 'json',
                cache: true,
                success: callback
            });
        }
    },
    
    /**
     * Fetch details for a dicument
     */
    documentDetails: function(id, callback) {
        options = {
            reference: id,
            output: 'consultations,attachments,thumbnails'}
        $.getJSON('/api/documents', options, callback);
    },
    
    /**
     * Formatiert ein ISO-Datum zum gebräuchlichen deutschen Format DD.MM.YYYY
     * @param   String   ISO-Datum (YYYY-MM-DD)
     * @return  String   Deutsches Datum
     */
    formatIsoDate: function(datestr){
        if (datestr != null && typeof datestr != "undefined") {
            var year = datestr.substr(0,4);
            var month = datestr.substr(5,2);
            var day = datestr.substr(8,2);
            return parseInt(day, 10) + '. ' + this.monthstr[month] + ' ' + year;
        }
    },
    
    truncateText: function(text, size){
        if (text.length <= size) {
            return text;
        }
        list = text.split(/\s+/);
        newtext = '';
        while (newtext.length < size) {
            newtext = newtext + ' ' + list.shift();
        }
        return newtext.trim() + '&nbsp;&hellip;';
    },
    
    fileSizeString: function(bytes){
        if (bytes < (1024 * 700)) {
            return Math.round(bytes / 1024) + ' KB';
        } else if (bytes < (1024 * 1024 * 5)) {
            return (bytes / 1024 / 1024).toFixed(1).replace('.', ',') + ' MB';
        }
    },
    
    /**
     * Takes an object of standard search parameters and deletes those which are default or null
     */
    processSearchParams: function(params){
        if (typeof params['q'] === 'undefined'
            || params['q'] == null
            || params['q'] === ''
            || params['q'] === '*:*') {
            delete params['q'];
        }
        if (typeof params['fq'] === 'undefined'
            || params['fq'] == null
            || params['fq'] === ''
            || params['fq'] === '*:*') {
            delete params['fq'];
        }
        if (typeof params['num'] == 'undefined'
            || params['num'] == null
            || params['num'] == ''
            || params['num'] <= 10) {
            delete params['num'];
        }
        if (typeof params['start'] == 'undefined'
            || params['start'] == null
            || params['start'] == ''
            || params['start'] <= 0) {
            delete params['start'];
        }
        if (typeof params['sort'] == 'undefined'
            || params['sort'] == null
            || params['sort'] == '') {
            delete params['sort'];
        }
         if (typeof params['date'] == 'undefined'
            || params['date'] == null
            || params['date'] == '') {
            delete params['date'];
        }
       return params;
    },
    
    deepCopy: function(obj) {
        if (typeof obj !== "object") return obj;
        if (obj.constructor === RegExp) return obj;
        
        var retVal = new obj.constructor();
        for (var key in obj) {
            if (!obj.hasOwnProperty(key)) continue;
            retVal[key] = OffenesKoeln.deepCopy(obj[key]);
        }
        return retVal;
    },
    
    search: function(params, callback){
        var cleanParams = OffenesKoeln.processSearchParams(params);
        $.getJSON('/api/documents', cleanParams, callback);
    },
    
    session: function(params, callback){
        $.getJSON('/api/session', params, callback);
    },
    
    /**
     * Verarbeitet das Placefinder Suchergebnis und sortiert
     * Einträge, die nicht zur Auswahl angezeigt werden sollen,
     * aus.
     */
    filterGeocodingChoices: function(results){
        results = OffenesKoeln.deepCopy(results);
        // Alle Einträge bekommen eigenen Qualitäts-Koeffizienten
        for (var n in results) {
            results[n].okquality = 1.0;
            // verdreifache wenn neighborhood gesetzt
            if (results[n].address.suburb != '') {
                results[n].okquality *= 3.0;
            }
            // verdopple wenn PLZ gesetzt
            if (results[n].address.postcode != '') {
                results[n].okquality *= 3.0;
            }
            // keine Straße gesetzt: Punktzahl durch 10
            if (typeof(results[n].address.road) === 'undefined') {
                results[n].okquality *= 0.1;
            }
        }
        // Sortieren nach 'okquality' abwärts
        results.sort(OffenesKoeln.qualitySort);
        var resultByPostCode = {};
        var n;
        for (n in results) {
            if (typeof(resultByPostCode[results[n].address.postcode]) === 'undefined') {
                resultByPostCode[results[n].address.postcode] = results[n];
            }
        }
        ret = [];
        for (n in resultByPostCode) {
            ret.push(resultByPostCode[n]);
        }
        // Sortieren nach Längengrad
        ret.sort(OffenesKoeln.longitudeSort);
        return ret;
    },
    
    qualitySort: function(a, b) {
        return b.okquality - a.okquality
    },

	longitudeSort: function(a, b) {
        return parseFloat(a.lon) - parseFloat(b.lon)
    },

	cylindrics: function(phi) {
		var	u = this.a * Math.cos(phi),
			v = this.b * Math.sin(phi),
			w = Math.sqrt(u * u + v * v),
			r = this.a * u / w,
			z = this.b * v / w,
			R = Math.sqrt(r * r + z * z);
		return { r : r, z : z, R : R };
	},
	
	/**
	 * Anstand zwischen zwei Geo-Koordinaten
	 * @param    phi1     Float    Länge Punkt 1
	 * @param    lon1     Float    Breite Punkt 1
	 * @param    phi2     Float    Länge Punkt 2
	 * @param    lon2     Float    Breite Punkt 3
	 * @param    small    Boolean  True für kleine Distanzen
	 */
	geo_distance: function(phi1, lon1, phi2, lon2, small) {
	    var dLambda = lon1 - lon2;
		with (cylindrics(phi1)) {
			var	r1 = r,
				z1 = z,
				R1 = R;
		}
		with (cylindrics(phi2)) {
			var	r2 = r,
				z2 = z,
				R2 = R;
		}
		var	cos_dLambda = Math.cos(dLambda),
			scalar_xy = r1 * r2 * cos_dLambda,
			cos_alpha = (scalar_xy + z1 * z2) / (R1 * R2);

		if (small) {
			var	dr2 = r1 * r1 + r2 * r2 - 2 * scalar_xy,
				dz2 = (z1 - z2) * (z1 - z2),
				R = Math.sqrt((dr2 + dz2) / (2 * (1 - cos_alpha)));
		}
		else R = Math.pow(a * a * b, 1/3);
		return R * Math.acos(cos_alpha);
	},

    /**
     * Aendert eine URL, so dass sie vom Offenes Koeln CDN ausgeliefert wird.
     * Dabei wird jede URL auf einen von mehreren Servern gemappt. Das Mapping
     * ist rekonstruierbar und verteilt die Anfragen möglichst gleichmäßig.
     *
     * @param   String  url   Vollstaendige URL der Datei
     */
    cdnify_url: function(url) {
        var hosts = ['a.ok.mycdn.de', 'b.ok.mycdn.de', 'c.ok.mycdn.de'];
        var res = 0;
        for (var i=0; i < url.length; i++) {
            res += url.charCodeAt(i) * (url.length - i);
        }
        var recoded = res.toString(hosts.length);
        var num = recoded.substr(recoded.length-1, 1);
        console.log(url, recoded, num, hosts[num]);
        var re = /^http[s]*:\/\/[^\/]+\/static/;
        return url.replace(re, 'http://'+hosts[num]);
    },

    /**
     * returns true if the string ends with given suffix
     */
    endsWith: function(str, suffix) {
        return str.indexOf(suffix, str.length - suffix.length) !== -1;
    }
};

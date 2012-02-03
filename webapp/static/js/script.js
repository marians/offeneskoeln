/**
 * offeneskoeln.de custom javascript
 * Author: Marian Steinbach
 */
var disqus_shortname = 'offeneskoeln';
var OffenesKoeln = {
    
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
        $.getJSON('/api/streets-by-position', {'lat': lat, 'lon': lon, 'radius': radius}, callback);
    },
    /**
     * returns a list of position coordinates for a street name,
     * as well as the average coordinates
     */
    positionsForName: function(name, list_nodes, callback) {
        var contain = ['result', 'average'];
        if (!list_nodes) {
            contain = ['average'];
        }
        $.getJSON('/api/positions-by-name', {'name': name, 'contain': contain.join(',')}, callback);
    },
    /**
     * Does the same as positionsForName, but for a list of names.
     * Requests are queued.
     */
    positionsForNamesQueued: function(names, callback) {
        for (var name in names) {
            $.ajaxq('positionsForNamesQueuedQueue', {
                url: "/api/positions-by-name",
                data: { name: names[name], contain: 'average'},
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
        $.getJSON('/api/document', {'id': id}, callback);
    },
    
    /**
     * Formatiert ein ISO-Datum zum gebräuchlichen deutschen Format DD.MM.YYYY
     * @param   String   ISO-Datum (YYYY-MM-DD)
     * @return  String   Deutsches Datum
     */
    formatIsoDate: function(datestr){
        var year = datestr.substr(0,4);
        var month = datestr.substr(5,2);
        var day = datestr.substr(8,2);
        return parseInt(day, 10) + '. ' + this.monthstr[month] + ' ' + year;
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
        if (bytes < (1024 * 800)) {
            return (bytes / 1024).toPrecision(2).replace('.', ',') + ' KB';
        } else {
            return (bytes / 1024 / 1024).toPrecision(2).replace('.', ',') + ' MB';
        }
    },
    
    /**
     * Takes an object of standard search parameters and deletes those which are default or null
     */
    processSearchParams: function(params){
        if (typeof params['q'] == 'undefined'
            || params['q'] == null
            || params['q'] == '' 
            || params['q'] == '*:*') {
            delete params['q'];
        }
        if (typeof params['fq'] == 'undefined' 
            || params['fq'] == null
            || params['fq'] == '' 
            || params['fq'] == '*:*') {
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
        $.getJSON('/api/query', cleanParams, callback);
    },
    
};

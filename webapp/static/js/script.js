/**
 */
var OpenRIS = {
  
  a: 6378137,
  b: (6378137 * 297.257223563) / 298.257223563,
  
  region: null,
  start_method_queue: new Array(),
  
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
   * Fetch details for a document
   */
  paperDetails: function(id, callback) {
    options = {
      reference: id,
      output: 'meetings,files,thumbnails'}
    $.getJSON('/api/paper', options, callback);
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
    return datestr;
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
    return(bytes);
  },
  
  /**
   * Takes an object of standard search parameters and deletes those which are default or null
   */
  processSearchParams: function(params){
    params['r'] = region_data['id']
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
      retVal[key] = OpenRIS.deepCopy(obj[key]);
    }
    return retVal;
  },
  
  search: function(params, callback){
    var cleanParams = OpenRIS.processSearchParams(params);
    $.getJSON('/api/papers', cleanParams, callback);
  },
  
  /* Sinn?
  session: function(params, callback){
    $.getJSON('/api/session', params, callback);
  },
  */
  
  /**
   * Verarbeitet das Placefinder Suchergebnis und sortiert
   * Einträge, die nicht zur Auswahl angezeigt werden sollen,
   * aus.
   */
  filterGeocodingChoices: function(results){
    results = OpenRIS.deepCopy(results);
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
    results.sort(OpenRIS.qualitySort);
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
    ret.sort(OpenRIS.longitudeSort);
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
    else
      R = Math.pow(a * a * b, 1/3);
      return R * Math.acos(cos_alpha);
  },

  /**
   * returns true if the string ends with given suffix
   */
  endsWith: function(str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
  },
  
  send_response: function(id) {
      alert(id);
      return false;
  }
};



/*
TODO: Make this better.
$(document).ready(function() {
  $('span.response').each(function(){
    $(this).click(function() {
      //alert($(this).attr('id').substring(11));
      $('#attachment_dialog').html(generateResponseContent($(this).attr('id').substring(11)));
      $('#attachment_response_form').submit(function(){
        var error = false;
        //TODO: form handling 
        if (!error) {
          data = {
            'id': $('#response_id').val(),
            'name': $('#response_name').val(),
            'email': $('#response_email').val(),
            'type': $('#response_type').val(),
            'message': $('#response_message').val(),
            'sent_on': window.location.href,
          }
          $.post('/api/response', data).done(function(data) {
            alert('Ihre Nachricht wurde gesendet.');
          });
          $('#attachment_dialog').dialog('close');
        }
        return(false);
      });
      $('#attachment_dialog').dialog('open');
    });
  });
  $('<div/>', {
    'id': 'attachment_dialog'
  }).appendTo('body');
  $('#attachment_dialog').dialog({
    autoOpen: false,
    draggable: false,
    width: 600,
    modal: true,
    title: 'Senden einer Rückmeldung zu einem Anhang'
  });
});

function generateResponseContent(id) {
  var html = ''
  html += '<form id="attachment_response_form">';
  html += '<p>Name</p>'
  html += '<input type="text" id="response_name" name="response_name" /></p>';
  html += '<p>E-Mail</p>'
  html += '<input type="text" id="response_email" name="response_email" /></p>';
  html += '<h3>Thema</h3>';
  html += '<select id="response_type">';
  html += '<option id="response_type_0" value="0">- bitte wählen -</option>';
  html += '<option id="response_type_2" value="2">Das Dokument verletzt Urheberrechte.</option>';
  html += '<option id="response_type_3" value="3">Das Dokument verletzt den Datenschutz.</option>';
  html += '<option id="response_type_4" value="4">Das Dokument hat / besteht aus leeren Seiten.</option>';
  html += '<option id="response_type_5" value="5">Das Dokument kann nicht geöffnet werden / die Datei ist beschädigt.</option>';
  html += '<option id="response_type_6" value="6">Das Dokument ist schwer lesbar.</option>';
  html += '<option id="response_type_7" value="7">Das Dokument hat gedrehte Seiten.</option>';
  html += '<option id="response_type_8" value="8">Das Dokument verfälscht die Suchergebnisse.</option>';
  html += '<option id="response_type_1" value="1">Ich habe eine andere Frage / Anregung / Rückmeldung.</option>';
  html += '</select>';
  html += '<h3>Nachricht</h3>';
  html += '<textarea id="response_message"></textarea>';
  html += '<input type="hidden" value="' + id + '" id="response_id" />';
  html += '<p><input type="submit" value="senden" /></p>';
  html += '</form>';
  
  return(html);
}
*/



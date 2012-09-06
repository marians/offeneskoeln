
$(document).ready(function(){
    var map = new L.Map('map');
    var maplayers = [];
    
    var cloudmadeUrl = 'http://{s}.tile.cloudmade.com/f838de29c9284d329bf4bcfbbcff32e3/52932/256/{z}/{x}/{y}.png',
        cloudmadeAttribution = 'Geodaten &copy; OpenStreetMap Mitwirkende, Darstellung &copy; 2011 CloudMade',
        cloudmade = new L.TileLayer(cloudmadeUrl, {
            maxZoom: 16,
            minZoom: 11,
            attribution: cloudmadeAttribution,
            unloadInvisibleTiles: true,
        });
    
    // geo bounds for cologne
    var lat_min = 50.87,
        lat_max = 51.04,
        lon_min = 6.8,
        lon_max = 7.1;
    
    // set to user position, if set and within cologne
    if (typeof position != "undefined" 
        && typeof position.lat != "undefined") {
        setUserPosition(position.lat, position.lon);
    } else {
        // center of cologne
        map.setView(new L.LatLng(50.9375, 6.944), 12).addLayer(cloudmade);
    }
    
    var locationPrompt = $('#position-prompt');
    if (locationPrompt.length > 0) {
        $('#street').focus();
    }
        
    // handle user data input
    $('#position-prompt-submit').click(function(evt){
        console.log("#position-prompt-submit click", evt);
        evt.preventDefault();
        $('#position-prompt .error').remove();
        $('#location-prompt-resultchoice').remove();
        var street = $('#street').val();
        var zip = $('#zip').val();
        // check if street is available
        if (street != '') {
            console.log("2. street is nicht leer", evt);
            data = {
                street: street,
                postal: zip
            }
            $.getJSON('/api/geocode-proxy', data, function(places){
                console.log('Placefinder response: ', places);
                if (places.ResultSet.Error != 0) {
                    handleLocationLookupError('SYSTEM');
                } else if (places.ResultSet.Found == 0) {
                    handleLocationLookupError('NOT_FOUND');
                } else if (places.ResultSet.Found == 1 && places.ResultSet.Results[0].radius > 1000) {
                    handleLocationLookupError('NEED_DETAILS');
                } else if (places.ResultSet.Found > 1) {
                    var choice = $(document.createElement('div')).attr('id', 'location-prompt-resultchoice');
                    choice.append('<span>Bitte wähle einen der folgenden Orte:</span><br />');
                    for (var n in places.ResultSet.Results) {
                        var choicelink = $(document.createElement('a')).attr('href', '#');
                        var resultObject = places.ResultSet.Results[n];
                        var choicetext = resultObject.street;
                        if (resultObject.neighborhood != '') {
                            choicetext += ' in ' + resultObject.neighborhood
                        }
                        if (resultObject.postal != '') {
                            choicetext += ' (' + resultObject.postal + ')'
                        }
                        choicelink.text(choicetext);
                        choicelink.click({resultObject:resultObject}, function(evt){
                            console.log(evt);
                            evt.preventDefault();
                            $('#street').val(evt.data.resultObject.street);
                            $('#zip').val(evt.data.resultObject.postal);
                            $('#location-prompt-resultchoice').remove();
                            setUserPosition(parseFloat(evt.data.resultObject.latitude), parseFloat(evt.data.resultObject.longitude));
                        });
                        choice.append(choicelink);
                        choice.append(' ');
                    }
                    locationPrompt.append(choice);
                } else {
                    setUserPosition(parseFloat(response.ResultSet.Results[0].latitude), parseFloat(response.ResultSet.Results[0].longitude));
                }
            });
        }
    });
    
    
    function handleLocationLookupError(reason){
        var msg = $(document.createElement('div')).attr('class', 'error');
        if (reason == 'NEED_DETAILS') {
            msg.append('Bitte gib den Ort genauer an, z.B. durch Angabe einer Hausnummer oder PLZ.');
        } else if (reson == 'NOT_FOUND') {
            msg.append('Der angegebene Ort wurde nicht gefunden. Bist Du sicher, dass er in Köln liegt?');
        } else {
            msg.append('Bei der Ortssuche ist ein unbekannter Fehler ausgetreten. Bitte versuche es noch einmal.');
        }
        locationPrompt.append(msg);
    }
    
    function setUserPosition(lat, lon) {
        var userLocation = new L.LatLng(lat, lon),
            radius = 500;
        
        $('#position-prompt').hide().after('<div id="map-claim">Sieh Dir an, was um Dich herum passiert:</div>');
        map.setView(userLocation, 14).addLayer(cloudmade);
        circleOptions = {color: '#97c66b', opacity: 0.4},
        circle = new L.Circle(userLocation, radius, circleOptions);
        maplayers.push(map.addLayer(circle));
        var streets = [];
        // save session - TODO: only if changed
        saveGeoPosition(lat, lon);
        // get surrounding streets for this position
        OffenesKoeln.streetsForPosition(lat, lon, radius, function(data){
            streets = data.result;
            // get marker positions for the surrounding streets
            var streetnames = [];
            for (var i in streets) {
                streetnames.push(streets[i][0]);
            }
            OffenesKoeln.positionsForNamesQueued(streetnames, function(data){
                if (data.average) {
                    $.getJSON('/api/query', {'fq': 'strasse:"'+ data.name +'"', 'docs': 1, 'sort': 'datum desc'}, function(search){
                        if (search.result.numhits > 0) {
                            var markerLocation = new L.LatLng(data.average[0], data.average[1]);
                            var marker = new L.Marker(markerLocation);
                            maplayers.push(map.addLayer(marker));
                            marker.bindPopup('<p><b><a href="/suche/?q=' + data.name + '">' + data.name + ': ' + search.result.numhits + ' Treffer</a></b><br/>Der jüngste vom ' + OffenesKoeln.formatIsoDate(search.result.docs[0].datum) + '</p>');
                        }
                    });
                }
            });
        })
    }
    
    /*
    map.on('click', onMapClick);
    var popup = new L.Popup();    
    function onMapClick(e) {
        var latlngStr = '(' + e.latlng.lat.toFixed(3) + ', ' + e.latlng.lng.toFixed(3) + ')';
        
        popup.setLatLng(e.latlng);
        popup.setContent("You clicked the map at " + latlngStr);
        map.openPopup(popup);
    }
    */
    
    /**
     * Speichert die zuletzt vom Nutzer angegebene Posiotion in der Session
     */
    function saveGeoPosition(latitude, longitude){
        $.getJSON('/api/setposition', {lat: latitude, lon: longitude}, function(data){});
    }
    
    /**
     * Callback function for navigator.geolocation.getCurrentPosition
     * in case of an error
     */
    function handleGeoPositionError(){
        console.log('handleGeoPositionError(): User has not specified position');
    }
    
    /**
     * Callback function for navigator.geolocation.getCurrentPosition
     * in case of success
     */
    function setGeoPositionFromNavigator(pos){
        if ( pos.coords.latitude > lat_min
        && pos.coords.latitude < lat_max
        && pos.coords.longitude > lon_min
        && pos.coords.longitude < lon_max) {
            setUserPosition(pos.coords.latitude, pos.coords.longitude);
        } else {
            console.log('User ist nicht in Köln :(');
        }
    }
    
    // ask user for position, if not yet set
    if (typeof position == "undefined"
        || typeof position.lat == "undefined") {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(setGeoPositionFromNavigator, handleGeoPositionError);
        }
    }
});

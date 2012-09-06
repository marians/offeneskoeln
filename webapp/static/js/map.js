
$(document).ready(function(){
    var map = new L.Map('map', {scrollWheelZoom: false});
    //var maplayers = [];
    var markerLayerGroup = new L.LayerGroup();
    map.addLayer(markerLayerGroup);
    
    // 'http://{s}.ok.mycdn.de/tiles/{z}/{x}/{y}.png'
    var tileUrlSchema = 'http://{s}.ok.mycdn.de/tiles/v2/{z}/{x}/{y}.png',
        attribution = '&copy; OpenStreetMap Mitwirkende',
        backgroundLayer = new L.TileLayer(tileUrlSchema, {
            maxZoom: 16,
            minZoom: 11,
            attribution: attribution
        });
    
    var sessionData = {}; // user session data
    
    var lastLocationEntry = ''; // die letzte vom User eingegebene Straße
    
    // geo bounds for cologne
    var lat_min = 50.87,
        lat_max = 51.04,
        lon_min = 6.8,
        lon_max = 7.1;
        
    map.setView(new L.LatLng(50.9375, 6.944), 11).addLayer(backgroundLayer);
    
    // set to user position, if set and within cologne
    OffenesKoeln.session({}, function(data){
        sessionData = data.response.session;
        //console.log("sessionData:", sessionData);
        if (typeof sessionData.location != 'undefined'
            && typeof sessionData.location.lat != 'undefined'
            && typeof sessionData.location.lon != 'undefined') {
                setUserPosition(parseFloat(sessionData.location.lat), 
                    parseFloat(sessionData.location.lon));
            if ($('#street').val() == '' && typeof sessionData.location.location_entry != 'undefined') {
                lastLocationEntry = sessionData.location.location_entry;
                $('#street').val(sessionData.location.location_entry);
            }
        } else {
            /*
            if (Modernizr.geolocation) {
                console.log("Asking Browser for location");
                navigator.geolocation.getCurrentPosition(setGeoPositionFromNavigator, handleGeoPositionError);
            }
            */
        }
    });
    
    var locationPrompt = $('#position-prompt');
    if (locationPrompt.length > 0) {
        $('#street').focus();
    }
        
    // handle user data input
    $('#position-prompt-submit').click(function(evt){
        evt.preventDefault();
        handleLocationInput();
    });
    $('#position-prompt-form').submit(function(evt){
        evt.preventDefault();
        handleLocationInput();
    });
    $('#street').keydown(function(evt){
        // Enter abfangen
        if (evt.keyCode == 13) {
            evt.preventDefault();
            $('#position-prompt-submit').trigger('click');
        }
    });
    $('#submit').click(function(evt){
        evt.preventDefault();
        $('#search-form').trigger('submit');
    });
    
    
    // Speichert die Session-Daten, aber setzt - anders als oben - 
    // die Karte nicht neu
    function handleSessionResponse(data){
        sessionData = data.response.session;
        //console.log("sessionData after handleSessionResponse:", sessionData);
    }
    
    function handleLocationInput() {
        resetMap();
        $('#position-prompt-submit');
        $('#position-prompt .spinner').css({visibility: 'visible'});
        //console.log("#position-prompt-submit click", evt);
        $('#position-prompt .error').remove();
        $('#location-prompt-resultchoice').remove();
        var street = $('#street').val();
        // check if street is available
        if (street != '') {
            data = {
                street: street,
            }
            $.getJSON('/api/proxy/geocode', data, function(places){
                $('#position-prompt .spinner').css({visibility: 'hidden'});
                //console.log('Placefinder response: ', places);
                if (places.ResultSet.Error != 0) {
                    handleLocationLookupError('SYSTEM');
                } else if (places.ResultSet.Found == 0) {
                    handleLocationLookupError('NOT_FOUND');
                } else {
                    var places_filtered = OffenesKoeln.filterPlacefinderChoices(places.ResultSet.Results);
                    if (places_filtered.length == 0) {
                        handleLocationLookupError('NOT_FOUND');
                    } else if (places_filtered.length > 1) {
                        // Nutzer muss aus mehreren Optionen auswählen
                        var choice = $(document.createElement('div'));
                        choice.attr('id', 'location-prompt-resultchoice');
                        choice.attr('class', 'content middle');
                        choice.css({display: 'none'});
                        choice.append('<div><span>Bitte wähle einen der folgenden Orte:</span></div>');
                        for (var n in places_filtered) {
                            // Marker auf der Karte
                            //console.log(places_filtered[n].woeid, places_filtered[n].latitude, places_filtered[n].longitude);
                            var markerLocation = new L.LatLng(parseFloat(places_filtered[n].latitude), parseFloat(places_filtered[n].longitude));
                            var marker = new L.Marker(markerLocation, {title: places_filtered[n].woeid});
                            marker.addEventListener("mouseover", function(evt){
                                // Achtung! ID des Highlight-Elements wird als title übergeben
                                $('#location-prompt-resultchoice a').removeClass('highlight');
                                $('#location-prompt-resultchoice .choicelink.' + evt.target.options.title).addClass('highlight');
                            });
                            marker.addEventListener("mouseout", function(evt){
                                $('#location-prompt-resultchoice a').removeClass('highlight');
                            });
                            marker.addEventListener("click", function(evt){
                                $('#location-prompt-resultchoice a').removeClass('highlight');
                                $('#location-prompt-resultchoice .choicelink.' + evt.target.options.title).trigger('click');
                            });
                            markerLayerGroup.addLayer(marker);
                            // Auswahllinks
                            var choicelink = $(document.createElement('a')).attr('href', '#');
                            var choicetext = '';
                            if (places_filtered[n].neighborhood != '') {
                                choicetext = places_filtered[n].neighborhood;
                            } else {
                                choicetext = places_filtered[n].street;
                            }
                            if (places_filtered[n].postal != '') {
                                choicetext += ' (' + places_filtered[n].postal + ')'
                            }
                            choicelink.text(choicetext);
                            choicelink.attr('class', 'choicelink ' + places_filtered[n].woeid);
                            choicelink.mouseover({resultObject:places_filtered[n], mapmarker: marker}, function(evt){
                                // Marker zentrieren und anzoomen
                                //console.log(evt.data);
                                map.setView(new L.LatLng(parseFloat(evt.data.resultObject.latitude), parseFloat(evt.data.resultObject.longitude)), 12);
                            });
                            choicelink.click({resultObject:places_filtered[n]}, function(evt){
                                //console.log(evt);
                                evt.preventDefault();
                                
                                $('#location-prompt-resultchoice').slideUp('fast', function(){
                                    $('#location-prompt-resultchoice').remove();
                                });
                                var entry_string = evt.data.resultObject.street;
                                if (evt.data.resultObject.house != '') {
                                    entry_string += ' ' + evt.data.resultObject.house;
                                }
                                if (evt.data.resultObject.postal != '') {
                                    entry_string += ' (' + evt.data.resultObject.postal + ')';
                                }
                                $('#street').val(entry_string);
                                lastLocationEntry = entry_string;
                                sessionParams = {
                                    'location_entry': entry_string, 
                                    'lat': evt.data.resultObject.latitude,
                                    'lon': evt.data.resultObject.longitude
                                };
                                setUserPosition(parseFloat(evt.data.resultObject.latitude), parseFloat(evt.data.resultObject.longitude));
                                OffenesKoeln.session(sessionParams, handleSessionResponse);
                            });
                            choice.append(choicelink);
                            choice.append(' ');
                        }
                        $('#position-form-container').after(choice);
                        $('#location-prompt-resultchoice').slideDown('fast');
                    } else {
                        // exakt ein Treffer
                        setUserPosition(parseFloat(places.ResultSet.Results[0].latitude), parseFloat(places.ResultSet.Results[0].longitude));
                        sessionParams = {'location_entry': street, 'lat': places.ResultSet.Results[0].latitude, 'lon': places.ResultSet.Results[0].longitude};
                        OffenesKoeln.session(sessionParams, handleSessionResponse);
                    }
                }
            });
        }
    }
    
    function clearMap() {
        markerLayerGroup.clearLayers();
    }
    
    function resetMap() {
        clearMap();
        map.setView(new L.LatLng(50.9375, 6.944), 11);
    }
    
    function handleChangePositionClick(evt) {
        evt.preventDefault();
        $('#map-claim').remove();
        $('#position-prompt').show();
        $('#street').focus();
        $('#street').select();
        resetMap();
    }
    
    function handleLocationLookupError(reason){
        var msg = $(document.createElement('div')).attr('class', 'error');
        if (reason == 'NEED_DETAILS') {
            msg.append('Bitte gib den Ort genauer an, z.B. durch Angabe einer Hausnummer oder PLZ.');
        } else if (reason == 'NOT_FOUND') {
            msg.append('Der angegebene Ort wurde nicht gefunden. Bist Du sicher, dass er in Köln liegt?');
        } else {
            msg.append('Bei der Ortssuche ist ein unbekannter Fehler ausgetreten. Bitte versuche es noch einmal.');
        }
        locationPrompt.append(msg);
    }
    
    function setUserPosition(lat, lon) {
        // Header-Element umbauen
        var streetString = $('#street').val();
        if (streetString == '') {
            streetString = sessionData.location.location_entry;
        }
        var changeLocationLink = $(document.createElement('a')).text(streetString).attr('href', '#').click(handleChangePositionClick);
        $('#position-prompt').slideUp().after('<div id="map-claim">Das passiert rund um </div>');
        $('#map-claim').append(changeLocationLink);
        // Karte umbauen
        clearMap();
        var userLocation = new L.LatLng(lat, lon),
            radius = 500;
        map.setView(userLocation, 14);
        circleOptions = {color: '#97c66b', opacity: 0.4},
        circle = new L.Circle(userLocation, radius, circleOptions);
        markerLayerGroup.addLayer(circle);
        var streets = [];
        // Straßen aus der Umgebung abrufen
        OffenesKoeln.streetsForPosition(lat, lon, radius, function(data){
            streets = data.response.streets;
            // get marker positions for the surrounding streets
            var streetnames = [];
            for (var i in streets) {
                streetnames.push(streets[i][0]);
            }
            OffenesKoeln.locationsForStreetsQueued(streetnames, function(data){
                if (data.response.averages) {
                    $.getJSON('/api/documents', {'fq': 'street:"'+ data.request.street +'"', 'docs': 1, 'sort': 'date desc'}, function(search){
                        if (search.response.numhits > 0) {
                            //console.log(search, data.response.averages[0]);
                            var markerLocation = new L.LatLng(data.response.averages[0][0], data.response.averages[0][1]);
                            var marker = new L.Marker(markerLocation);
                            markerLayerGroup.addLayer(marker);
                            var markerHtml = '<p><b><a href="/suche/?q=' + data.request.street + '">' + data.request.street + ': ' + search.response.numhits + ' Treffer</a></b>';
                            if (search.response.documents[0].date && search.response.documents[0].date[0]) {
                                markerHtml += '<br/>Der jüngste vom ' + OffenesKoeln.formatIsoDate(search.response.documents[0].date[0]);
                            } else {
                                //console.log('Kein Datum: ', search.response.documents[0]);
                            }
                            markerHtml += '</p>';
                            marker.bindPopup(markerHtml);
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
     * Speichert die zuletzt vom Nutzer angegebene Position in der Session
     */
    function saveGeoPosition(latitude, longitude){
        $.getJSON('/api/session', {lat: latitude, lon: longitude}, function(data){});
    }
    
    /**
     * Callback function for navigator.geolocation.getCurrentPosition
     * in case of an error
     */
    function handleGeoPositionError(){
        //console.log('handleGeoPositionError(): User has not specified position');
    }
    
    /**
     * Callback function for navigator.geolocation.getCurrentPosition
     * in case of success
     */
    function setGeoPositionFromNavigator(pos){
        console.log('setGeoPositionFromNavigator:', pos);
        if ( pos.coords.latitude > lat_min
        && pos.coords.latitude < lat_max
        && pos.coords.longitude > lon_min
        && pos.coords.longitude < lon_max) {
            setUserPosition(pos.coords.latitude, pos.coords.longitude);
            sessionParams = {'lat': pos.coords.latitude, 'lon': pos.coords.longitude};
            OffenesKoeln.session(sessionParams, handleSessionResponse);
        } else {
            console.log('User ist nicht in Köln :(');
        }
    }
});

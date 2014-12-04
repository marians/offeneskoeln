
$(document).ready(function(){
  var map = new L.Map('map', {/*scrollWheelZoom: false*/});
  //var maplayers = [];
  var markerLayerGroup = new L.LayerGroup();
  map.addLayer(markerLayerGroup);
  
  var backgroundLayer = new L.TileLayer(CONF.mapTileUrlSchema, {
      maxZoom: CONF.mapTileMaxZoom,
      minZoom: CONF.mapTileMinZoom,
      attribution: CONF.mapTileAttribution
    });
  
  var sessionData = {}; // user session data
  
  var lastLocationEntry = ''; // die letzte vom User eingegebene Strasse
  
  map.setView(new L.LatLng(51.165691, 10.451526), 6).addLayer(backgroundLayer);
  
  /*
  Alternative tile config. This tile-set should only be used for testing.
  // OSM Copyright Notice
  L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: 'Map &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);
  */
  
  // set to user position, if set and within cologne
  OpenRIS.session({}, function(data){
    sessionData = data.response;
    //console.log("sessionData:", sessionData);
    if (typeof sessionData != 'undefined' &&
      typeof sessionData.lat != 'undefined' &&
      typeof sessionData.lon != 'undefined' &&
      sessionData.lat !== '' && sessionData.lon !== '' &&
      sessionData.lat !== null && sessionData.lon !== null) {
        setUserPosition(parseFloat(sessionData.lat),
          parseFloat(sessionData.lon));
      if ($('#street').val() === '' && typeof sessionData.location_entry != 'undefined') {
        lastLocationEntry = sessionData.location_entry;
        $('#street').val(sessionData.location_entry);
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
    sessionData = data.response;
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
    if (street !== '') {
      data = {
        street: street
      };
      $.getJSON('/api/proxy/geocode', data, function(places){
        $('#position-prompt .spinner').css({visibility: 'hidden'});
        console.log('Geocoding response: ', places);
        if (places.result.length === 0) {
          handleLocationLookupError('NOT_FOUND');
        } else {
          var places_filtered = OpenRIS.filterGeocodingChoices(places.result);
          if (places_filtered.length === 0) {
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
              //console.log(places_filtered[n].lat, places_filtered[n].lon);
              var markerLocation = new L.LatLng(parseFloat(places_filtered[n].lat), parseFloat(places_filtered[n].lon));
              var marker = new L.Marker(markerLocation, {title: places_filtered[n].osm_id});
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
              if (places_filtered[n].address.suburb !== '') {
                choicetext = places_filtered[n].address.suburb;
              } else {
                choicetext = places_filtered[n].address.road;
              }
              if (places_filtered[n].address.postcode !== '') {
                choicetext += ' (' + places_filtered[n].address.postcode + ')';
              }
              choicelink.text(choicetext);
              choicelink.attr('class', 'choicelink ' + places_filtered[n].osm_id);
              choicelink.mouseover({resultObject:places_filtered[n], mapmarker: marker}, function(evt){
                // Marker zentrieren und anzoomen
                map.setView(new L.LatLng(parseFloat(evt.data.resultObject.lat), parseFloat(evt.data.resultObject.lon)), 12);
              });
              choicelink.click({resultObject:places_filtered[n]}, function(evt){
                //console.log(evt);
                evt.preventDefault();
                
                $('#location-prompt-resultchoice').slideUp('fast', function(){
                  $('#location-prompt-resultchoice').remove();
                });
                var entry_string = evt.data.resultObject.address.road;
                if (evt.data.resultObject.address.postcode !== '') {
                  entry_string += ' (' + evt.data.resultObject.address.postcode + ')';
                }
                $('#street').val(entry_string);
                lastLocationEntry = entry_string;
                sessionParams = {
                  'location_entry': entry_string,
                  'lat': evt.data.resultObject.lat,
                  'lon': evt.data.resultObject.lon
                };
                setUserPosition(parseFloat(evt.data.resultObject.lat), parseFloat(evt.data.resultObject.lon));
                OpenRIS.session(sessionParams, handleSessionResponse);
              });
              choice.append(choicelink);
              choice.append(' ');
            }
            $('#position-form-container').after(choice);
            $('#location-prompt-resultchoice').slideDown('fast');
          } else {
            // exakt ein Treffer
            setUserPosition(parseFloat(places.result[0].lat), parseFloat(places.result[0].lon));
            sessionParams = {
              'location_entry': street,
              'lat': places.result[0].lat,
              'lon': places.result[0].lon
            };
            OpenRIS.session(sessionParams, handleSessionResponse);
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
    map.setView(new L.LatLng(CONF.mapStartPoint[1], CONF.mapStartPoint[0]), 11);
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
      msg.append('Der angegebene Ort wurde nicht gefunden. Bist Du sicher, dass er in '+ 'TODO' +' liegt?');
    } else {
      msg.append('Bei der Ortssuche ist ein unbekannter Fehler ausgetreten. Bitte versuche es noch einmal.');
    }
    locationPrompt.append(msg);
  }
  
  function setUserPosition(lat, lon) {
    // Header-Element umbauen
    var streetString = $('#street').val();
    if (streetString === '') {
      streetString = sessionData.location_entry;
    }
    var changeLocationLink = $(document.createElement('span')).text(streetString).attr({'id': 'map-claim-street'});
    var newSearchLink = $(document.createElement('a')).text('Neue Suche').attr({'href': '#', 'class': 'awesome extrawide'}).css('margin-left', '20px').click(handleChangePositionClick);
    var article = '';
    if (OpenRIS.endsWith(streetString, 'straße') || OpenRIS.endsWith(streetString, 'gasse')) {
      article = 'die';
    }
    var mapClaim = '<div id="map-claim"><span>Das passiert rund um ' + article + ' </span></div>';
    $('#position-prompt').slideUp().after(mapClaim);
    $('#map-claim').append(changeLocationLink).append(newSearchLink);
    // Karte umbauen
    clearMap();
    var userLocation = new L.LatLng(lat, lon),
      radius = 500;
    map.setView(userLocation, 14);
    var circleOptions = {color: '#97c66b', opacity: 0.7, fill: false, draggable: true};
    var outerCircle = new L.Circle(userLocation, radius, circleOptions);
    var innerDot = new L.Circle(userLocation, 20, {fillOpacity: 0.9, fillColor: '#97c66b', stroke: false, draggable: true});
    var positionPopup = L.popup()
        .setLatLng(userLocation)
        .setContent('<p>Dies ist der Suchmittelpunkt für die Umkreissuche.</p>');
    outerCircle.on('click', function(e){
      map.openPopup(positionPopup);
    });
    outerCircle.on('drag', function(e){
      console.log(e);
    });
    innerDot.on('click', function(e){
      map.openPopup(positionPopup);
    });
    markerLayerGroup.addLayer(outerCircle);
    markerLayerGroup.addLayer(innerDot);
    var streets = [];
    // Strassen aus der Umgebung abrufen
    OpenRIS.streetsForPosition(lat, lon, radius, function(data){
      //console.log('streetsForPosition callback data: ', data);
      
      if (typeof data.response.streets !== 'undefined') {
        // version 1 API response
        var streetnames = [];
        var streets = data.response.streets;
        for (var i in data.response.streets) {
          streetnames.push(data.response.streets[i][0]);
        }
        // get marker positions for the surrounding streets
        OpenRIS.locationsForStreetsQueued(streetnames, function(data){
          if (data.response.averages) {
            $.getJSON('/api/documents', {'fq': 'street:"'+ data.request.street +'"', 'docs': 1, 'sort': 'date desc'}, function(search){
              if (search.response.numhits > 0) {
                //console.log(search, data.response.averages[0]);
                var markerLocation = new L.LatLng(data.response.averages[0][0], data.response.averages[0][1]);
                var marker = new L.Marker(markerLocation);
                markerLayerGroup.addLayer(marker);
                var markerHtml = '<p><b><a href="/suche/?q=' + data.request.street + '">' + data.request.street + ': ' + search.response.numhits + ' Treffer</a></b>';
                if (search.response.documents[0].date && search.response.documents[0].date[0]) {
                  markerHtml += '<br/>Neuster Treffer vom ' + OpenRIS.formatIsoDate(search.response.documents[0].date[0]);
                } else {
                  //console.log('Kein Datum: ', search.response.documents[0]);
                }
                markerHtml += '</p>';
                marker.bindPopup(markerHtml);
              }
            });
          }
        });
      } else {
        // version 2 API response
        streets_by_name = {};
        var name;
        // collect streets by name
        for (var j in data.response) {
          name = data.response[j].name;
          if (typeof streets_by_name[name] === 'undefined') {
            streets_by_name[name] = [];
          }
          streets_by_name[name].push(data.response[j]);
        }
        // do search by name
        $.each(streets_by_name, function(name, street) {
          //console.log(name, streets_by_name[name].length);
          $.getJSON('/api/documents', {'q': name, 'docs': 1, 'sort': 'date desc'}, function(search){
            if (search.response.numhits > 0) {
              //console.log("Search result for", name, search);
              //console.log("Street object", name, streets_by_name[name]);
              // draw path for street (experimental)
              $.each(streets_by_name[name], function(n, streetpart){
                var points = [];
                //console.log(streetpart);
                $.each(streetpart.nodes, function(n, node){
                  points.push(new L.LatLng(
                    node.location.coordinates[1], node.location.coordinates[0]
                  ));
                });
                var markerHtml = '<p><b><a href="/suche/?q=' + name + '">' + name + ': ' + search.response.numhits + ' Treffer</a></b>';
                if (search.response.documents[0].date && search.response.documents[0].date[0]) {
                  markerHtml += '<br/>Der jüngste vom ' + OpenRIS.formatIsoDate(search.response.documents[0].date);
                }
                markerHtml += '</p>';
                var polyline = L.polyline(points, {color: '#ff0909'});
                polyline.bindPopup(markerHtml);
                markerLayerGroup.addLayer(polyline);
              });
            }
          });
        });
      }
    });
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
  /*
  function setGeoPositionFromNavigator(pos){
    console.log('setGeoPositionFromNavigator:', pos);
    if ( pos.coords.latitude > lat_min &&
      pos.coords.latitude < lat_max &&
      pos.coords.longitude > lon_min &&
      pos.coords.longitude < lon_max) {
      setUserPosition(pos.coords.latitude, pos.coords.longitude);
      sessionParams = {'lat': pos.coords.latitude, 'lon': pos.coords.longitude};
      OpenRIS.session(sessionParams, handleSessionResponse);
    } else {
      console.log('User ist nicht in Köln :(');
    }
  }
  */
});

$(document).ready(function(){
  // region click
  $('#change-region').click(function(){
    $.getJSON('/api/regions', function(data) {
      $.each(data, function(region_id, region){
        $('#region-question').css({'display': 'none'});
        $('<span/>')
          .text(region['name'])
          .attr({'class': 'awesome extrawide'})
          .click(
            {'region': region},
            function(event) {
              region_data = {
                'id': event.data.region.id,
                'name': event.data.region.name,
                'lat': event.data.region.lat,
                'lon': event.data.region.lon,
                'zoom': event.data.region.zoom
              }
              OpenRIS.region = event.data.region;
              $('#region-choice').html('');
              $('#region-question').css({'display': 'block'});
              update_region();
              if (typeof(OpenRIS.post_region_change) == 'function') {
                OpenRIS.post_region_change();
              }
            }
          )
          .appendTo('#region-choice');
      });
    });
  });
});

function update_region() {
  // update region name
  $('#region-current').text(OpenRIS.region.name);
  // update street description
  if (OpenRIS.region.type == 1)
    $('#address-label').text('Straße:');
  else
    $('#address-label').text('Straße und Stadt:');
  // update search examples
  if ($('#search-examples')) {
    $('#search-examples').html('');
    $('#search-examples').append(document.createTextNode('Beispiele: '));
    $.each(OpenRIS.region.keyword, function(id, keyword){
      $('<a/>')
        .text(keyword)
        .attr({'href': '/suche/?q=' + encodeURI(keyword)})
        .appendTo('#search-examples');
      if (OpenRIS.region.keyword.length > id + 1)
        $('#search-examples').append(document.createTextNode(', '));
    });
  }
}
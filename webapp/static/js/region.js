$(document).ready(function(){
  // get region in session
  $.getJSON('/api/session', function(data){
    OffenesKoeln.region = data['response']['region'];
    update_region();
  });
  
  // region click
  $('#change-region').click(function(){
    $.getJSON('/api/regions', function(data) {
      $.each(data, function(region_id, region){
        $('#region-question').css({'display': 'none'});
        $('<span/>')
          .text(region['name'])
          .attr({'class': 'awesome extrawide'})
          .click(
            {'region_id': region_id, 'region': region},
            function(event) {
              OffenesKoeln.region = event.data.region;
              $.getJSON('/api/session', {'region_id': OffenesKoeln.region.region_id}, function(data){});
              $('#region-choice').html('');
              $('#region-question').css({'display': 'block'});
              update_region();
            }
          )
          .appendTo('#region-choice');
      });
    });
  });
});

function update_region() {
  // update region name
  $('#region-current').text(OffenesKoeln.region.name);
  // update street description
  if (OffenesKoeln.region.type == 1)
    $('#address-label').text('Straße:');
  else
    $('#address-label').text('Straße und Stadt:');
  // update search examples
  if ($('#search-examples')) {
    $('#search-examples').html('');
    $('#search-examples').append(document.createTextNode('Beispiele: '));
    $.each(OffenesKoeln.region.search_examples, function(id, keyword){
      $('<a/>')
        .text(keyword)
        .attr({'href': '/suche/?q=' + encodeURI(keyword)})
        .appendTo('#search-examples');
      if (OffenesKoeln.region.search_examples.length > id + 1)
        $('#search-examples').append(document.createTextNode(', '));
    });
  }
}
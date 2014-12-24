$(document).ready(function() {
  OpenRIS.regionLoad();
  
  if (typeof openris_search_settings != undefined) {
    $('#search .result').empty();
    $('#search .result').append('<div class="loading big outer"><div class="loading big inner">Suche...</div></div>');
    var search_parms = OpenRIS.deepCopy(openris_search_settings);
    search_parms['output'] = 'facets';
    OpenRIS.search(
      search_parms,
      function(data) {
        $('#search .result').empty();
        $('#facets').remove();
        if (data.status == 0) {
          if (typeof data.response.facets != 'undefined') {
            $('#search-form').after('<div id="facets" class="content middle"></div>');
            displaySearchResultFacets(data.response.facets, data.request, '#facets');
          }
          displaySearchResult(data);
          displayPagerWidget(data.response.numhits, openris_search_settings.ppp, data.response.start, '#search .result');
          if (data.response.numhits > 1) {
            displaySortWidget(data.request, '#search .result h3');
          }
        } else {
          displaySearchErrorMessage();
        }
      }
    );
  }

  $('#search-submit').click(function(evt){
    evt.preventDefault();
    $('#region_input').val(region_data['id'])
    $('#searchform').trigger('submit');
  });
  $('#searchform').submit(function(evt) {
    $('#region_input').val(region_data['id'])
  })
  
  // register post region change actions
  OpenRIS.post_region_change = function() {
    $('#region_input').val(region_data['id'])
    $('#searchform').trigger('submit');
  }
  
  /*
  $('#qinput').makeAutocompleteSearchField({
		formSelector: '#searchform',
		inputSelector: '#qinput',
	});
  */
  
  /**
   * Sort a facet object {key: value, ...}
   *
   * @param   data  Object to sort
   * @param   String  Either "key" or "value"
   */
  function sortFacet(data, field) {
		var newlist = [];
		for (var i in data) {
			newlist.push({key: i, value: data[i]});
		}
		if (field == 'key') {
			newlist.sort(sortCompareByKey);
		} else if (field == 'value') {
			newlist.sort(sortCompareByValue);
		}
		return newlist;
	}
	function sortCompareByKey(a, b) {
		return b.key - a.key;
	}
	function sortCompareByValue(a, b) {
		return b.value - a.value;
	}
	
  function displaySearchResultFacets(facets, query, targetSelector) {
    if (typeof facets != 'undefined') {
      //create obj of string
      fq = query.fq
      var rest = true
      x = 0
      result = new Object();
      while (rest) {
        y = fq.indexOf(":", x);
        if (y == -1)
          break
        temp = fq.substring(x, y);
        x = y + 1
        if (fq.substring(x, x+5) == "&#34;") {
          y = fq.indexOf("&#34;", x+5);
          if (y == -1)
            break
          result[temp] = fq.substring(x+5, y)
          x = y + 6;
          if (x > fq.length)
            break
        }
        else {
          y = fq.indexOf(";", x);
          if (y == -1) {
            result[temp] = fq.substring(x, fq.length);
            break
          }
          else {
            result[temp] = fq.substring(x, y);
            x = y + 1
          }
        }
      }
      
      // paperType facet
      paperType_facet = createSearchResultFacet('paperType', facets.paperType, 'Typ', 'value', result);
      $(targetSelector).append(paperType_facet);
      bodyName_facet = createSearchResultFacet('bodyName', facets.bodyName, 'Körperschaft', 'value', result);
      $(targetSelector).append(bodyName_facet);
      // gremium facet
      //organization_facet = createSearchResultFacet('organization', facets.organization, 'Gremium', 'value', result, true);
      //$(targetSelector).append(organization_facet);
      // schlagwort facet
      //term_facet = createSearchResultFacet('term', facets.term, 'Stichwort', 'value', query.fq, true);
      //$(targetSelector).append(term_facet);
      // schlagwort datum
      publishedDate_facet = createSearchResultFacet('publishedDate', facets.publishedDate, 'Erstellungsdatum', '', result, true);
      $(targetSelector).append(publishedDate_facet);
    }
  }
  
  /**
   * Creates a search result facet and returns the HTMLElement object
   *
   * @param   String  name    Name of the facet
   * @param   Object  data    facet data object, unsorted
   * @param   String  headline  Header to display
   * @param   String  sortField   'key' or 'value'
   * @param   String  fq      filter query currently applied
   * @param   Boolean filterIds   True to filter out numeric ids in front of labels, false to leave as is
   */
  function createSearchResultFacet(name, data, headline, sortField, fq, filterIds) {
    var facet_data = sortFacet(data, sortField);
    var facet = $(document.createElement('div')).attr('class', 'facet ' + name);
    var list = $(document.createElement('ul')).attr('class', 'facet');
    // currently filtered by this facet
    if (fq[name]) {
      var label = fq[name];
      if (name=='publishedDate')
        label=OpenRIS.monthstr[label.substr(5,7)] + " " + label.substr(0,4);
      if (filterIds == true) {
        label = label.replace(/^[0-9]+\s+/, '');
      }
      var sqs = ''
      for (var i in fq) {
        if (i != name) {
          if (sqs)
            sqs += ';';
          sqs += i + ':' + quoteFacetValue(fq[i]);
        }
        
      }
      if (!sqs)
        sqs = null
      list.append('<li class="current"><a title="Diese Einschränkung aufheben" href="/suche/?'+ (searchQueryString({fq: sqs })) +'"><span class="facetdel">&#10005;</span><span class="facetlabel">'+ label.replace(/&#34;/g, "") +'</span></a></li>');
    }
    else {
      for (var i in facet_data) {
        var label = facet_data[i].key;
        if (filterIds == true)
          label = label.replace(/^[0-9]+\s+/, '');
        if (name=='publishedDate')
          label=OpenRIS.monthstr[label.substr(5,7)] + " " + label.substr(0,4);
        var sqs;
        if (!openris_search_settings['fq'])
          sqs = name + ':' + quoteFacetValue(facet_data[i].key);
        else
          sqs = openris_search_settings['fq'] + ';' + name + ':' + quoteFacetValue(facet_data[i].key);
        list.append('<li><a href="/suche/?'+ (searchQueryString({fq: sqs })) +'"><span class="facetlabel">'+ label +'</span> <span class="num">'+ facet_data[i].value +'</span></a></li>');
      }
    }
    facet.append('<div class="header">'+ headline +'</div>');
    facet.append(list);
    return facet;
  }
  
  /**
   * Packt Facetten-Werte in Anführungszeichen, wenn sie ein Leerzeichen enthalten
   */
  function quoteFacetValue(str) {
    if (str.indexOf(' ') != -1) {
      str = '"' + str + '"';
    }
    return str;
  }
  
  function displaySearchErrorMessage(){
    $('#search .result').append('<h2>Fehler bei der Suche</h2><p>Es ist ein unerwarteter Fehler aufgetreten. Bitte probier es noch einmal.</p><p>Wenn das Problem weiterhin besteht, bitte kopiere den Inhalt der Adresszeile in eine E-Mail und sende sie an <a href="mailto:kontakt@offeneskoeln.de">kontakt@offeneskoeln.de</a>. Vielen Dank!</p>');
  }
  
  function displaySearchResult(data) {
    var result = $('#search .result');
    
    // headline
    $('h1').text(data.response.numhits + ' gefundene Dokumente');
    if (data.response.numhits > 0) {
      var subheadline = $(document.createElement('h3'));
      subheadline.text('Seite ' + (Math.floor(data.response.start / openris_search_settings.ppp)+1) + ' von ' + (Math.ceil(data.response.numhits / openris_search_settings.ppp)));
      result.append(subheadline);
    }
    
    // results ol
    var resultlist = $(document.createElement('ol'));
    resultlist.attr('start', data.response.start + 1);
    result.append(resultlist);
    for (var i in data.response.result) {
      var item = $(document.createElement('li')).attr('class','resultitem');
      resultlist.append(item);
      var link = $(document.createElement('a')).attr('href', '/paper/' + data.response.result[i]['id']);
      item.append(link);
      var title = $(document.createElement('span')).attr('class','title').html(itemName(data.response.result[i]));
      link.append(title);
      var metainfo = $(document.createElement('span')).attr('class','metainfo');
      metainfo.text(createMetaInfoText(data.response.result[i]));
      link.append(metainfo);
      var snippet = $(document.createElement('p')).attr('class','snippet');
      snippet.html(createSnippet(data.response.result[i]));
      item.append(snippet);
    }
  }
  
  /**
   * Generate the output title and apply, if possible, search term highlighting
   */
  function itemName(paper) {
    if (paper.name !== '') {
      if (typeof paper.highlighting != 'undefined' &&
        typeof paper.highlighting.title != 'undefined') {
        return paper.highlighting.title;
      }
      return paper.name;
    } else {
      return 'Dokument ohne Name';
    }
  }
  
  function createMetaInfoText(document) {
    return document.paperType + ' aus ' + document.bodyName + ' vom ' + OpenRIS.formatIsoDate(document.publishedDate)
  }
  
  function createSnippet(document) {
    return '... ' + document.fileFulltext + ' ...'
  }
  
  /**
   * @param   numhits   Number of items in search result
   * @param   rows  Number of rows per page
   * @param   start   Current offset
   */
  function displayPagerWidget(numhits, rows, start, targetSelector) {
    var pager = $(document.createElement('div'));
    pager.attr('class', 'pager');
    $(targetSelector).append(pager);
    // previous page
    if (start > 0) {
      pager.append('<a class="awesome extrawide paging back" href="/suche/?'+ searchQueryString({start: (start - openris_search_settings.ppp)}) +'">&larr; &nbsp; Seite zurück</a>');
    }
    pager.append(' ');
    // next page
    if (numhits > (start + rows)) {
      pager.append('<a class="awesome extrawide paging next" href="/suche/?'+ searchQueryString({start: (start + openris_search_settings.ppp)}) +'">Seite weiter &nbsp; &rarr;</a>');
    }
  }
  
  /**
   * Kontrollelement zur Anzeige der aktuellen Sortierung und zum
   * Aendern der Sortierung
   *
   * @param   Object  data         Request-Parameter
   * @param   String  targetSelector   jQuery Selector zur Bestimmgung des DOM-Elements für die Ausgabe
   */
  function displaySortWidget(data, targetSelector) {
    var widget = $(document.createElement('span'));
    widget.attr('class', 'sort');
    $(targetSelector).append(widget);
    widget.append(' &ndash; sortiert nach ');
    var parts = [];
    var sortOptions = {
      'score:desc': 'Relevanz',
      'publishedDate:desc': 'Datum: neuste zuerst',
      'publishedDate:asc': 'Datum: älteste zuerst'
    };
    for (var o in sortOptions) {
      if (data.sort == o) {
        parts.push('<b>' + sortOptions[o] + '</b>');
      } else {
        parts.push('<a href="/suche/?'+ searchQueryString({sort: o, start: 0}) +'">' + sortOptions[o] + '</a>');
      }
    }
    widget.append(parts.join(' | '));
  }
  
  /**
   * creates a search query string for a modified search.
   * Takes parameters from openris_search_settings and overrides parameters
   * given in
   * @param   overwrite
   */
  function searchQueryString(overwrite) {
    var settings = OpenRIS.deepCopy(openris_search_settings);
    for (var item in overwrite) {
      if (overwrite[item] == null 
        || typeof overwrite[item] == 'undefined') {
        delete settings[item];
      } else {
        settings[item] = overwrite[item];
      }
      
    }
    settings = OpenRIS.processSearchParams(settings);
    var parts = []
    for (var item in settings) {
      parts.push(item + '=' + encodeURI(settings[item]));
    }
    return parts.join('&');
  }
});

/**
 * Search field autocompletion
 * Author: Marian Steinbach <marian@sendung.de>
 
(function($){
	var displayAutocompleteTerms = function(rows, options) {
		$(options.flyoutSelector).empty();
		// display autocomplete suggestions
		for (var key in rows) {
			var newrow = $('<a class="autocompleterow" href="#">' + rows[key][0] + '</a>');
			newrow.click(function(event){
				event.stopPropagation();
				event.preventDefault();
				submitSearch($(this).text());
			});
			$(options.flyoutSelector).append(newrow);
		}
	};
	$.fn.extend({
		makeAutocompleteSearchField: function(options) {
			// option defaults
			var defaults = {
				keyWaitTime: 250,
				preventEnterSubmit: false,
				inputSelector: '#queryinput',
				flyoutSelector: '#searchflyout',
				yoffset: 5,
				numAutocompleteRows: 10
			};
			var options =  $.extend(defaults, options);
			var call;
			if ($('#searchflyout').length == 0) {
				$('body').append('<div id="searchflyout"></div>');
			}
			return this.each(function() {
				var o = options;
				var obj = $(this);
				var selectedAutocomplete, selectedItem;
				handleQueryStringChange = function() {
					querystring = $(obj).val();
					if (querystring == '') {
						hideFlyout();
					} else {
						$.getJSON('/api/terms', {prefix: querystring}, function(data){
							displayAutocompleteTerms(data, options);
							showFlyout();
						});
					}
					selectedAutocomplete = undefined;
					selectedItem = undefined;
				};
				showFlyout = function() {
					var x = obj.offset().left;
					var y = obj.offset().top + obj.height() + o.yoffset;
					var w = obj.width();
					$(o.flyoutSelector).css({top: y, left: x, 'min-width': w});
					$(o.flyoutSelector).show();
					$('html').click(function() {
						hideFlyout();
					});
				};
				submitSearch = function(term) {
					hideFlyout();
					updateSearchField(term);
					$(obj).focus();
					$(o.formSelector).submit();
				};
				hideFlyout = function() {
					$(o.flyoutSelector).hide();
				};
				setSelection = function(delta) {
					if (delta > 0) {
						if (typeof selectedAutocomplete == 'undefined') {
							selectedAutocomplete = 0;
						} else {
							selectedAutocomplete = Math.min(selectedAutocomplete + 1, o.numAutocompleteRows - 1);
						}
					} else {
						if (selectedAutocomplete == 0) {
							selectedAutocomplete = undefined;
						} else if (typeof selectedAutocomplete != 'undefined') {
							selectedAutocomplete -= 1;
						}
					}
					$(o.flyoutSelector).find('.selected').removeClass('selected');
					if (typeof selectedAutocomplete != 'undefined') {
						$($(o.flyoutSelector).find('.autocompleterow')[selectedAutocomplete]).addClass('selected');
					}
				};
				selectCurrentItem = function() {
					// submits the search or goes to linked item
					if (typeof selectedAutocomplete != 'undefined') {
						submitSearch( $($(o.flyoutSelector).find('.selected')).text());
					}
				};
				updateSearchField = function(term){
					$(obj).val(term);
				};
				$(obj).keydown(function(event){
					if (event.keyCode == 40 // down
						|| event.keyCode == 38 // up
						) {
						event.preventDefault();
					}
				});
				$(obj).keyup(function(event){
					event.preventDefault();
					if (event.keyCode == 40) {
						// arrow down
						setSelection(1);
						return false;
					} else if (event.keyCode == 38) {
						// arrow up
						setSelection(-1);
						return false;
					} else if (event.keyCode == 13) {
						// return or space key
						window.clearTimeout(call);
						selectCurrentItem();
					} else 	if (event.keyCode == 27) {
						// esc
						hideFlyout();
					} else if (
						event.keyCode == 91 // cmd left
						|| event.keyCode == 93 // cmd right
						|| event.keyCode == 18 // alt
						|| event.keyCode == 16 // shift
						|| event.keyCode == 20 // shift lock
						|| event.keyCode == 37 // arrow left
						|| event.keyCode == 39 // arrow right
						) {
						// do nothing!
					} else {
						window.clearTimeout(call);
						call = window.setTimeout(handleQueryStringChange, o.keyWaitTime);
					}
				});
				$(o.formSelector).submit(function(){
					hideFlyout();
				});
			});
		}
	});
})(jQuery);
*/
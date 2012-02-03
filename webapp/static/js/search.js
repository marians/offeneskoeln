$(document).ready(function(){
    if (typeof ok_search_settings != undefined) {
        $('#search .result').empty();
        $('#search .result').append('<div class="loading big outer"><div class="loading big inner">Suche...</div></div>');
        //console.log("Page search settings:", ok_search_settings);
        var search_parms = OffenesKoeln.deepCopy(ok_search_settings);
        search_parms['facets'] = 1;
        OffenesKoeln.search(
            search_parms,
            function(response) {
                //console.log('query response:', data);
                $('#search .result').empty();
                $('#facets').remove();
                if (response.status == 0) {
                    if (typeof response.result.facets != 'undefined') {
                        $('#search .content.middle').after('<div id="facets" class="content middle"></div>');
                        displaySearchResultFacets(response.result.facets, response.params, '#facets');
                    }
                    displaySearchResult(response);
                    displayPagerWidget(response.result.numhits, ok_search_settings.num, response.result.start, '#search .result');
                    if (response.result.numhits > 1) {
                        displaySortWidget(response.result, '#search .result h3');
                    }
                } else {
                    displaySearchErrorMessage();
                }
            }
        );

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
     * @param   data    Object to sort
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
        console.log(query.fq);
        if (typeof facets != 'undefined') {
            // typ facet
            typ_facet = createSearchResultFacet('typ', facets.typ, 'Typ', 'value', query.fq);
            $(targetSelector).append(typ_facet);
            // gremium facet
            gremium_facet = createSearchResultFacet('gremium', facets.gremium, 'Gremium', 'value', query.fq, true);
            $(targetSelector).append(gremium_facet);
            // schlagwort facet
            schlagwort_facet = createSearchResultFacet('schlagwort', facets.schlagwort, 'Stichwort', 'value', query.fq, true);
            $(targetSelector).append(schlagwort_facet);
        }
    }
    
    /**
     * Creates a search result facet and returns the HTMLElement object
     *
     * @param   String  name        Name of the facet
     * @param   Object  data        facet data object, unsorted
     * @param   String  headline    Header to display
     * @param   String  sortField   'key' or 'value'
     * @param   String  fq          filter query currently applied
     * @param   Boolean filterIds   True to filter out numeric ids in front of labels, false to leave as is
     */
    function createSearchResultFacet(name, data, headline, sortField, fq, filterIds) {
        var facet_data = sortFacet(data, sortField);
        var facet = $(document.createElement('div')).attr('class', 'facet ' + name);
        var list = $(document.createElement('ul')).attr('class', 'facet');
        if (fq.indexOf(name) != -1) {
            // currently filtered by this facet
            var re = new RegExp(name + ':"([^"]+)"');
            var find = fq.match(re);
            if (find) {
                var label = find[1];
                if (filterIds == true) {
                    label = label.replace(/^[0-9]+\s+/, '');
                }
                list.append('<li class="current"><a title="Diese Einschränkung aufheben" href="/suche/?'+ (searchQueryString({fq: null })) +'"><span class="del">&#10005;</span><span class="label">'+ label +'</span></a></li>');
            }
            
        } else {
            for (var i in facet_data) {
                var label = facet_data[i].key;
                if (filterIds == true) {
                    label = label.replace(/^[0-9]+\s+/, '');
                }
                list.append('<li><a href="/suche/?'+ (searchQueryString({fq: name + ':&quot;' + facet_data[i].key +'&quot;' })) +'"><span class="label">'+ label +'</span> <span class="num">'+ facet_data[i].value +'</span></a></li>');
            }
        }
        facet.append('<div class="header">'+ headline +'</div>');
        facet.append(list);
        return facet;
    }
    
    function displaySearchErrorMessage(){
        $('#search .result').append('<p>Fehler bei der Suche.</p><p>TODO: Diese Fehlermeldung aufhübschen.</p>');
    }
    
    function displaySearchResult(data) {
        var result = $('#search .result');
        
        // headline
        $('h1').text(data.result.numhits + ' gefundene Dokumente');
        var subheadline = $(document.createElement('h3'));
        //console.log(data.start, ok_search_settings.num);
        subheadline.text('Seite ' + (Math.floor(data.result.start / ok_search_settings.num)+1) + ' von ' + (Math.floor(data.result.numhits / ok_search_settings.num)+1));
        result.append(subheadline);
        
        // results ol
        var resultlist = $(document.createElement('ol'));
        resultlist.attr('start', data.result.start+1);
        result.append(resultlist);
        for (var i in data.result.docs) {
            var item = $(document.createElement('li')).attr('class','resultitem');
            resultlist.append(item);
            var id = data.result.docs[i].aktenzeichen.replace(/\//g, '-');
            var link = $(document.createElement('a')).attr('href', '/dokumente/' + id + '/');
            item.append(link);
            var title = $(document.createElement('span')).attr('class','title').html(itemTitle(data.result.docs[i], data.result.highlighting));
            link.append(title);
            var snippet = $(document.createElement('span')).attr('class','snippet');
            snippet.text(snippetText(data.result.docs[i]));
            link.append(snippet);
        }
    }
    
    /**
     * Generate the output title and apply, if possible, search term highlighting
     */
    function itemTitle(document, highlights) {
        if (document.betreff != '') {
            if (typeof highlights[document.id].betreff != 'undefined' && typeof highlights[document.id].betreff[0] != 'undefined') {
                return highlights[document.id].betreff[0];
            }
            return document.betreff;
        } else {
            return 'Dokument ohne Titel';
        }
    }
    
    function snippetText(document) {
        return document.typ + ' ' + document.aktenzeichen + ' vom ' + OffenesKoeln.formatIsoDate(document.datum);
    }
    
    /**
     * @param   numhits     Number of items in search result
     * @param   rows    Number of rows per page
     * @param   start   Current offset
     */
    function displayPagerWidget(numhits, rows, start, targetSelector) {
        var pager = $(document.createElement('div'));
        pager.attr('class', 'pager');
        $(targetSelector).append(pager);
        // previous page
        if (start > 0) {
            pager.append('<a class="back" href="/suche/?'+ searchQueryString({start: (start - ok_search_settings.num)}) +'">Seite zurück</a>');
        }
        pager.append(' ');
        // next page
        if (numhits > (start + rows)) {
            pager.append('<a class="next" href="/suche/?'+ searchQueryString({start: (start + ok_search_settings.num)}) +'">Seite weiter</a>');
        }
    }
    
    function displaySortWidget(data, targetSelector) {
        var widget = $(document.createElement('span'));
        widget.attr('class', 'sort');
        $(targetSelector).append(widget);
        widget.append(' &ndash; sortiert nach ');
        var parts = [];
        var sortOptions = {
            'score desc': 'Relevanz',
            'datum desc': 'Datum: neuste zuerst',
            'datum asc': 'Datum: älteste zuerst'
        }
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
     * Takes parameters from ok_search_settings and overrides parameters
     * given in 
     * @param   overwrite
     */
    function searchQueryString(overwrite) {
        var settings = OffenesKoeln.deepCopy(ok_search_settings);
        for (var item in overwrite) {
            if (overwrite[item] == null 
                || typeof overwrite[item] == 'undefined') {
                delete settings[item];
            } else {
                settings[item] = overwrite[item];
            }
            
        }
        settings = OffenesKoeln.processSearchParams(settings);
        var parts = []
        for (var item in settings) {
            parts.push(item + '=' + settings[item]);
        }
        return parts.join('&');
    }
   
});

/**
 * Search field autocompletion
 * Author: Marian Steinbach <marian@sendung.de>
 */
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

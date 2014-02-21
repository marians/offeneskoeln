$(document).ready(function() {
    search_wait();
});

// ugly way of waiting for region data
function search_wait() {
    if (!OffenesKoeln.region)
        setTimeout(function() { search_wait(); }, 10);
    else
        search_start();
}

function search_start() {
    if (typeof ok_search_settings != undefined) {
        $('#search .result').empty();
        $('#search .result').append('<div class="loading big outer"><div class="loading big inner">Suche...</div></div>');
        //console.log("Page search settings:", ok_search_settings);
        var search_parms = OffenesKoeln.deepCopy(ok_search_settings);
        search_parms['output'] = 'facets';
        //console.log(search_parms)
        console.log(OffenesKoeln.region);
        OffenesKoeln.search(
            search_parms,
            function(data) {
                //console.log('query response:', data);
                $('#search .result').empty();
                $('#facets').remove();
                if (data.status == 0) {
                    if (typeof data.response.facets != 'undefined') {
                        $('#search .content.middle').after('<div id="facets" class="content middle"></div>');
                        displaySearchResultFacets(data.response.facets, data.request, '#facets');
                    }
                    displaySearchResult(data);
                    displayPagerWidget(data.response.numhits, ok_search_settings.num, data.response.start, '#search .result');
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
        $('#searchform').trigger('submit');
    });
    
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
            
            // typ facet
            type_facet = createSearchResultFacet('type', facets.type, 'Typ', 'value', result);
            $(targetSelector).append(type_facet);
            // gremium facet
            committee_facet = createSearchResultFacet('committee', facets.committee, 'Gremium', 'value', result, true);
            $(targetSelector).append(committee_facet);
            // schlagwort facet
            //term_facet = createSearchResultFacet('term', facets.term, 'Stichwort', 'value', query.fq, true);
            //$(targetSelector).append(term_facet);
            // schlagwort datum
            date_facet = createSearchResultFacet('date', facets.date, 'Zeitraum', '', result, true);
            $(targetSelector).append(date_facet);
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
        console.log(fq[name])
        // currently filtered by this facet
        if (fq[name]) {
            console.log(fq)
            var label = fq[name];
            if (name=='date')
                label=OffenesKoeln.monthstr[label.substr(5,7)] + " " + label.substr(0,4);
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
            list.append('<li class="current"><a title="Diese Einschränkung aufheben" href="/suche/?'+ (searchQueryString({fq: sqs })) +'"><span class="del">&#10005;</span><span class="label">'+ label.replace(/&#34;/g, "") +'</span></a></li>');
        }
        else {
            for (var i in facet_data) {
                var label = facet_data[i].key;
                if (filterIds == true)
                    label = label.replace(/^[0-9]+\s+/, '');
                if (name=='date')
                    label=OffenesKoeln.monthstr[label.substr(5,7)] + " " + label.substr(0,4);
                var sqs;
                if (!ok_search_settings['fq'])
                    sqs = name + ':' + quoteFacetValue(facet_data[i].key);
                else
                    sqs = ok_search_settings['fq'] + ';' + name + ':' + quoteFacetValue(facet_data[i].key);
                list.append('<li><a href="/suche/?'+ (searchQueryString({fq: sqs })) +'"><span class="label">'+ label +'</span> <span class="num">'+ facet_data[i].value +'</span></a></li>');
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
        //console.log(data);
        var result = $('#search .result');
        
        // headline
        $('h1').text(data.response.numhits + ' gefundene Dokumente');
        if (data.response.numhits > 0) {
            var subheadline = $(document.createElement('h3'));
            subheadline.text('Seite ' + (Math.floor(data.response.start / ok_search_settings.num)+1) + ' von ' + (Math.ceil(data.response.numhits / ok_search_settings.num)));
            result.append(subheadline);
        }
        
        // results ol
        var resultlist = $(document.createElement('ol'));
        resultlist.attr('start', data.response.start + 1);
        result.append(resultlist);
        for (var i in data.response.documents) {
            var item = $(document.createElement('li')).attr('class','resultitem');
            resultlist.append(item);
            var link = $(document.createElement('a')).attr('href', data.response.documents[i].url); // Backup: .replace(/%2F/, '/')
            item.append(link);
            var title = $(document.createElement('span')).attr('class','title').html(itemTitle(data.response.documents[i]));
            link.append(title);
            var snippet = $(document.createElement('span')).attr('class','snippet');
            snippet.text(snippetText(data.response.documents[i]));
            link.append(snippet);
        }
    }
    
    /**
     * Generate the output title and apply, if possible, search term highlighting
     */
    function itemTitle(document) {
        if (document.title !== '') {
            if (typeof document.highlighting != 'undefined' &&
                typeof document.highlighting.title != 'undefined') {
                return document.highlighting.title;
            }
            return document.title;
        } else {
            return 'Dokument ohne Titel';
        }
    }
    
    function snippetText(document) {
        return document.type + ' ' + document.reference + ' vom ' + OffenesKoeln.formatIsoDate(document.date);
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
            pager.append('<a class="awesome extrawide paging back" href="/suche/?'+ searchQueryString({start: (start - ok_search_settings.num)}) +'">&larr; &nbsp; Seite zurück</a>');
        }
        pager.append(' ');
        // next page
        if (numhits > (start + rows)) {
            pager.append('<a class="awesome extrawide paging next" href="/suche/?'+ searchQueryString({start: (start + ok_search_settings.num)}) +'">Seite weiter &nbsp; &rarr;</a>');
        }
    }
    
    /**
     * Kontrollelement zur Anzeige der aktuellen Sortierung und zum
     * Aendern der Sortierung
     *
     * @param   Object  data               Request-Parameter
     * @param   String  targetSelector     jQuery Selector zur Bestimmgung des DOM-Elements für die Ausgabe
     */
    function displaySortWidget(data, targetSelector) {
        var widget = $(document.createElement('span'));
        widget.attr('class', 'sort');
        $(targetSelector).append(widget);
        widget.append(' &ndash; sortiert nach ');
        var parts = [];
        var sortOptions = {
            'score desc': 'Relevanz',
            'date desc': 'Datum: neuste zuerst',
            'date asc': 'Datum: älteste zuerst'
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
            parts.push(item + '=' + encodeURI(settings[item]));
        }
        return parts.join('&');
    }
   
}

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

$(document).ready(function(){
    var disqus_title = '';
    var disqus_category_id = 'dokument';
    
    var thumbs_data = {}; // speichert Details zu den Thumbs aller Attachments
    
    /**
     * Zoomt die Thumbnail-Darstellung von Höhe 300 auf 800
     */
    function zoomThumbsClick(evt) {
        //console.log('zoomThumbs', evt.data);
        evt.preventDefault();
        // alle img src-Attribute umschreiben
        $('.at' + evt.data.attachment_id + ' img').each(function(index){
            var img = $(this);
            var target_height = 800;
            var target_width = thumbs_data[evt.data.attachment_id][800].images[index].width;
            img.animate({width: target_width, height: target_height}, {duration: 400, easing: 'swing'});
            img.attr('src', img.attr('src').replace('-300', '-800'));
            img.parent('a').replaceWith(img);
        });
        // Breite des Thumbs-Containers zuerst setzen, ohne Animation
        $('.at' + evt.data.attachment_id + ' .thumbsinner').css({width: thumbs_data[evt.data.attachment_id][800].width});
        // Animation
        $('.at' + evt.data.attachment_id + ' .thumbs').animate({height: '825px'}, {duration: 300, easing: 'swing'});
        $('.at' + evt.data.attachment_id + ' .thumbsinner').animate({height: '810px'}, {duration: 300, easing: 'swing'});
    }
    if (ok_document_id){
        OffenesKoeln.documentDetails(ok_document_id, function(data){
            //console.log(data);
            if (data.status == 0) {
                
                // title and H1
                var title = data.response.documents[0].title[0];
                disqus_title = 'Dokument ' + ok_document_id;
                $('.content.middle').remove();
                $('title').text(title);
                $('.content.top').append($(document.createElement('h1')).text(title));
                
                // Beratungsfolge
                // TODO: Mehr Details hinzufügen, wenn verfügbar
                var consultationdiv = $(document.createElement('div'));
                consultationdiv.attr('class', 'consultation content middle');
                consultationdiv.append('<h2>Sitzungen</h2>');
                var consultation = $(document.createElement('ol'));
                //consultation.attr('class', 'metadata consultation');
                var num_consultations = 0;
                for (var d in data.response.documents) {
                    for (var c in data.response.documents[d].consultations) {
                        var litext = data.response.documents[d].consultations[c].committee_name;
                        litext += ', ' + (data.response.documents[d].consultations[c].date ? OffenesKoeln.formatIsoDate(data.response.documents[d].consultations[c].date) : 'Datum unbekannt');
                        num_consultations += 1;
                        consultation.append($(document.createElement('li')).text(litext));
                    }
                }
                consultationdiv.append(consultation);
                
                // Anzahl Attachments
                var num_attachments = 0;
                for (var d in data.response.documents) {
                    if (typeof data.response.documents[d].attachments != 'undefined') {
                        num_attachments += data.response.documents[d].attachments.length;
                    }
                }
                
                // Link zu RIS
                var ris_urls = [];
                for (var d in data.response.documents) {
                    for (var u in data.response.documents[d].original_url) {
                        ris_urls.push(data.response.documents[d].original_url[u]);
                    }
                }
                var ris_link = '';
                if (ris_urls.length > 1) {
                    var ris_links = [];
                    for (var u in ris_urls) {
                        ris_links.push('<a href="'+ ris_urls[u] +'" target="_blank">Dokument ' + (u + 1) + '</a>');
                    }
                    ris_link = 'Ratsinformationssystem der Stadt Köln ' + ris_links.join(', ');
                } else {
                    ris_link = '<a href="'+ ris_urls[0] +'" target="_blank">Ratsinformationssystem der Stadt Köln<a>';
                }
                
                // document type and date
                var metadata_table = $(document.createElement('table'));
                metadata_table.attr('class', 'metadata');
                metadata_table.append('<tr><td class="label">Art des Dokuments:</td><td class="value">'+ data.response.documents[0].type.join('<br />') +'</td></tr>');
                metadata_table.append('<tr><td class="label">Erstellt am:</td><td class="value">'+ (data.response.documents[0].date[0] ? OffenesKoeln.formatIsoDate(data.response.documents[0].date[0]) : 'Datum unbekannt') +'</td></tr>');
                metadata_table.append('<tr><td class="label">Beraten in:</td><td class="value">'+ num_consultations +' Sitzung'+ (num_consultations != 1 ? 'en' : '') +'</td></tr>');
                metadata_table.append('<tr><td class="label">Anlagen:</td><td class="value">'+ num_attachments +' Datei'+ (num_attachments != 1 ? 'en' : '') +'</td></tr>');
                metadata_table.append('<tr><td class="label">Quelle:</td><td class="value">'+ ris_link +'</td></tr>');
                $('.content.top').append(metadata_table);
                
                $('.content.top').after(consultationdiv);
                
                // attachments
                var attachments = $(document.createElement('div'));
                attachments.attr('class', 'attachments content middle');
                attachments.append('<h2>'+ data.response.documents[0].attachments.length +' Anlagen</h2>')
                $('.consultation').after(attachments);
                
                for (var a in data.response.documents[0].attachments) {
                    var attachment = data.response.documents[0].attachments[a];
                    var attachmentdiv = $(document.createElement('div'));
                    attachmentdiv.attr('class', 'attachment at' + attachment.id);
                    attachmentdiv.append('<h3>'+ attachment.role +'</h3>');
                    attachments.append(attachmentdiv);
                    //console.log(attachment.exclusion);
                    if (attachment.exclusion) {
                        var reasonhtml = '<p class="exclusionheader">Es tut uns leid, aber dieses Dokument wurde enfernt. Die Begründung:</p>';
                        reasonhtml += '<p class="reasontext">'+ attachment.exclusion.reason_text +'</p>';
                        reasonhtml += '<p>Weitere Informationen dazu gibt es <a href="http://blog.offeneskoeln.de/post/18377162772/abmahnung-und-selbstzensur" target="_blank">in unserem Blog</a>.</p>';
                        attachmentdiv.append('<div class="attachmentexclusion">'+ reasonhtml +'</div>');
                    } else {
                        // thumbnails
                        if (attachment.numpages) {
                            var h3el = $('.at' + attachment.id + ' h3');
                            //console.log(h3el, h3el.text());
                            if (attachment.numpages > 1) {
                                h3el.text(h3el.text() + ' ('+ attachment.numpages +' Seiten)');
                            }
                            attachmentdiv.append('<div class="thumbs"><div class="thumbsinner"></div></div>');
                            var twidth = 0; // width of all thumbs side by side, including border and margins
                            thumbs_data[attachment.id] = {};
                            for (var t in attachment.thumbnails) {
                                if (typeof thumbs_data[attachment.id][attachment.thumbnails[t].height] == 'undefined') {
                                    thumbs_data[attachment.id][attachment.thumbnails[t].height] = {
                                        num_thumbs: 0,
                                        width: 0,
                                        attachment_id: attachment.id,
                                        images: []
                                    };
                                }
                                var turl = OffenesKoeln.cdnify_url(attachment.thumbnails[t].url);
                                var imgtag = '<img class="thumb" src="'+ turl +'" width="'+ attachment.thumbnails[t].width +'" height="'+ attachment.thumbnails[t].height +'" />';
                                
                                // Alle Thumbs strukturiert in thumbs_data ablegen
                                if (attachment.thumbnails[t].height == 300 || attachment.thumbnails[t].height == 800) {
                                    thumbs_data[attachment.id][attachment.thumbnails[t].height].num_thumbs += 1;
                                    thumbs_data[attachment.id][attachment.thumbnails[t].height].width += attachment.thumbnails[t].width + 7;
                                    thumbs_data[attachment.id][attachment.thumbnails[t].height].images.push({
                                        tag: imgtag,
                                        width: attachment.thumbnails[t].width,
                                        url: OffenesKoeln.cdnify_url(attachment.thumbnails[t].url)
                                    });
                                }
                                
                                if (attachment.thumbnails[t].height == 300) {
                                    var thumblink = $(document.createElement('a')).attr('href', '#').click({
                                        attachment_id: attachment.id, 
                                        height: attachment.thumbnails[t].height,
                                        index: t
                                    }, zoomThumbsClick);
                                    thumblink.append(imgtag);
                                    $('.at' + attachment.id + ' .thumbsinner').append(thumblink);
                                    twidth += attachment.thumbnails[t].width + 7;
                                }
                            }
                            $('.at' + attachment.id + ' .thumbsinner').css({'width': twidth, 'height': 310}); // inner div needs fixed width and height
                            
                        }
                        // Volltextanzeige
                        if (typeof attachment.content != 'undefined') {
                            var fulltext_content = $.trim(attachment.content);
                            if (fulltext_content !== '') {
                                var truncated_html = OffenesKoeln.truncateText(fulltext_content, 200);
                                var fulltext_div = $(document.createElement('div')).attr('class', 'fulltext');
                                var truncated_div = $(document.createElement('div')).attr('class', 'truncated').html(truncated_html);
                                fulltext_div.append(truncated_div);
                                if (fulltext_content.length > truncated_html.length) {
                                    truncated_div.append(' ');
                                    var expand_text_link = $(document.createElement('a')).attr('href', '#').text('Gesamten Text anzeigen');
                                    expand_text_link.click({attachment: attachment}, function(e){
                                        e.preventDefault();
                                        console.log(e.data.attachment);
                                        $('.at' + e.data.attachment.id + ' .truncated').hide();
                                        var complete_fulltext_div = $(document.createElement('div')).attr('class', 'complete').html(e.data.attachment.content);
                                        complete_fulltext_div.hide();
                                        $('.at' + e.data.attachment.id + ' .fulltext').append(complete_fulltext_div);
                                        complete_fulltext_div.slideDown();
                                    });
                                    truncated_div.append(expand_text_link);
                                }
                                attachmentdiv.append(fulltext_div);
                            }
                        }
                        attachmentdiv.append('<div class="actions"><a target="_blank" href="'+ attachment.url.replace('http://localhost:8080/', 'http://offeneskoeln.de/') +'" class="awesome">Anhang öffnen</a> <span class="typesize">'+ OffenesKoeln.fileSizeString(attachment.size) +'</span></div>');
                        if (attachment.type == 'application/pdf') {
                            $('.at' + attachment.id + ' .typesize').append(' PDF &ndash; <a title="öffnet das PDF mit Google Docs Viewer" href="https://docs.google.com/viewer?url='+ encodeURI(attachment.url.replace('http://localhost:8080/', 'http://offeneskoeln.de/')) +'" target="_blank">Vorschau</a>');
                        }
                    }
                }
                
                // Disqus
                $('.content.bottom').append('<div class="comments"><h2>Kommentare, Fragen, Ergänzungen</h2></div>');
                $('.comments').append('<div id="disqus_thread"></div>');
                
                /* * * DON'T EDIT BELOW THIS LINE * * */
                (function() {
                    var dsq = document.createElement('script'); dsq.type = 'text/javascript'; dsq.async = true;
                    dsq.src = 'http://' + disqus_shortname + '.disqus.com/embed.js';
                    (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(dsq);
                })();
            }
        });
        
         
    }
});

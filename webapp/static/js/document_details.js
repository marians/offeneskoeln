$(document).ready(function(){
    var disqus_title = '';
    var disqus_category_id = 'dokument';
    if (ok_document_id){
        OffenesKoeln.documentDetails(ok_document_id, function(data){
            //console.log(data);
            if (data.status == 0) {
                
                // title and H1
                var title = '';
                if (data.documents.length == 1) {
                    title = data.documents[0].subject;
                } else {
                    title = 'TODO: Mehrere Dokumente mit dieser ID';
                }
                disqus_title = 'Dokument ' + ok_document_id.replace('-', '/');
                $('.content.middle').remove();
                $('title').text(title);
                $('.content.top').append($(document.createElement('h1')).text(title));
                
                // H2 with document type and date
                var metadata = $(document.createElement('p'));
                metadata.attr('class', 'metadata type');
                if (data.documents[0].type == 'submission') {
                    metadata.text(data.documents[0].submission_type + ' vom ' + OffenesKoeln.formatIsoDate(data.documents[0].date));
                } else {
                    metadata.text('Antrag vom ' + OffenesKoeln.formatIsoDate(data.documents[0].date));
                }
                $('.content.top').append(metadata);
                
                // consultation sequence
                // TODO: add more details as soon as scraper is fixed and agendaitems are correct
                var consultationdiv = $(document.createElement('div'));
                consultationdiv.attr('class', 'consultation content middle');
                consultationdiv.append('<h2>Sitzungen</h2>');
                var consultation = $(document.createElement('ol'));
                //consultation.attr('class', 'metadata consultation');
                for (var s in data.documents[0].sessions) {
                    consultation.append($(document.createElement('li')).text(data.documents[0].sessions[s].session_title));
                }
                consultationdiv.append(consultation);
                $('.content.top').after(consultationdiv);
                
                // attachments
                var attachments = $(document.createElement('div'));
                attachments.attr('class', 'attachments content middle');
                attachments.append('<h2>'+ data.documents[0].attachments.length +' Anlagen</h2>')
                $('.consultation').after(attachments);
                
                for (var a in data.documents[0].attachments) {
                    var attachment = $(document.createElement('div'));
                    attachment.attr('class', 'attachment at' + data.documents[0].attachments[a].attachment_id);
                    attachment.append('<h3>'+ data.documents[0].attachments[a].attachment_role +'</h3>');
                    attachments.append(attachment);
                    // thumbnnails
                    if (data.documents[0].attachments[a].num_pages) {
                        var h3el = $('.at' + data.documents[0].attachments[a].attachment_id + ' h3');
                        //console.log(h3el, h3el.text());
                        if (data.documents[0].attachments[a].num_pages > 1) {
                            h3el.text(h3el.text() + ' ('+ data.documents[0].attachments[a].num_pages +' Seiten)');
                        }
                        attachment.append('<div class="thumbs"><div class="thumbsinner"></div></div>');
                        $.getJSON('/api/attachment-thumbs', {id: data.documents[0].attachments[a].attachment_id}, function(th){
                            var twidth = 0; // width of all thumbs side by side, including border and margins
                            for (var t in th.thumbs) {
                                if (th.thumbs[t].height == 300) {
                                    $('.at' + th.id + ' .thumbsinner').append('<img class="thumb" src="'+ th.thumbs[t].uri +'" width="'+ th.thumbs[t].width +'" height="'+ th.thumbs[t].height +'" />');
                                    twidth += th.thumbs[t].width + 7;
                                }
                            }
                            $('.at' + th.id + ' .thumbsinner').css({'width': twidth, 'height': 310}); // inner div needs fixed width and height
                        });
                    }
                    if (data.documents[0].attachments[a].attachment_content != null && data.documents[0].attachments[a].attachment_content.length > 0) {
                        attachment.append('<div class="content">'+ OffenesKoeln.truncateText(data.documents[0].attachments[a].attachment_content, 400) +'</div>');
                    }
                    attachment.append('<div class="actions"><a target="_blank" href="'+ data.documents[0].attachments[a].attachment_uri +'">Herunterladen</a> ('+ OffenesKoeln.fileSizeString(data.documents[0].attachments[a].attachment_size) +')</div>');
                    //attachment.append($(document.createElement('li')).text(data.documents[0].attachments[a].role));
                    
                }
                
                // Link zu RIS
                $('.attachments').after('<div class="external content middle"><a href="'+ data.documents[0].original_url +'" target="_blank">Dieses Dokument im Ratsinformationssystem der Stadt Köln</a></div>');
                
                
                // Disqus
                $('.content.bottom').append('<div class="comments"><h2>Kommentare</h2></div>');
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

$(document).ready(function(){
    
    var thumbs_data; // speichert Details zu den Thumbs aller Attachments
    
    /**
     * Progressive enhancement zur Verkürzung der angezeigten texte
     */
    function truncateFulltext() {
        $('.attachment').each(function(n, attachment){
            var attachment_id = $(attachment).attr('id');
            $(attachment).find('.fulltext').each(function(n, fulltext){
                var fulltext_content = $('#' + attachment_id + ' .complete .text').html();
                var truncated_html = OffenesKoeln.truncateText(fulltext_content, 350);
                var truncated_div = $('<div class="truncated"><div class="text">' + truncated_html + '</div></div>');
                $(fulltext).append(truncated_div);
                $('#' + attachment_id + ' .complete').hide();
                if (fulltext_content.length > truncated_html.length) {
                    var expand_text_link = $(document.createElement('a')).attr('href', '#').text('Gesamten Text anzeigen');
                    expand_text_link.click({
                        attachment_id: attachment_id,
                        content: fulltext_content
                    }, function(e){
                        e.preventDefault();
                        // hide truncated text div (for later re-use)
                        $('#' + e.data.attachment_id + ' .truncated').hide();
                        $('#' + e.data.attachment_id + ' .complete').slideDown();
                    });
                    $('#' + attachment_id + ' .truncated').append(expand_text_link);
                }
            });
        });
    }

    /**
     * Zoomt die Thumbnail-Darstellung von Höhe 300 auf 800
     */
    function zoomThumbsClick(evt) {
        //console.log('zoomThumbs', evt.data);
        evt.preventDefault();
        // alle img src-Attribute umschreiben
        $('#' + evt.data.attachment_id + ' img').each(function(index){
            var img = $(this);
            var target_height = 800;
            var target_width = thumbs_data[evt.data.attachment_id][800].images[index].width;
            img.animate({width: target_width, height: target_height}, {duration: 400, easing: 'swing'});
            img.attr('src', img.attr('src').replace('/300/', '/800/'));
            img.parent('a').replaceWith(img);
        });
        // Breite des Thumbs-Containers zuerst setzen, ohne Animation
        $('#' + evt.data.attachment_id + ' .thumbsinner').css({width: thumbs_data[evt.data.attachment_id][800].width});
        // Animation zur Vergroesserung des Thumbnails-Containers
        $('#' + evt.data.attachment_id + ' .thumbs').animate({height: '825px'}, {duration: 300, easing: 'swing'});
        $('#' + evt.data.attachment_id + ' .thumbsinner').animate({height: '810px'}, {duration: 300, easing: 'swing'});
    }

    /**
     * Liest Informationen über alle Thumbnails zu allen Attachments
     * und befüllt thumbs_data
     */
    function readThumbnailData(data) {
        thumbs_data = {};
        $.each(data.response.documents[0].attachments, function(i, attachment){
            thumbs_data[attachment._id] = {};
            $.each(attachment.thumbnails, function(height, heightthumbs){
                if (height == 300 || height == 800) {
                    thumbs_data[attachment._id][height] = {
                        num_thumbs: 0,
                        width: 0,
                        images: []
                    };
                    $.each(attachment.thumbnails[height], function(index, thumb){
                        thumbs_data[attachment._id][height].num_thumbs += 1;
                        thumbs_data[attachment._id][height].width += thumb.width + 11;
                        thumbs_data[attachment._id][height].images.push({
                            width: thumb.width,
                            url: thumb.url
                        });
                    });
                }
            });
        });
    }

    /**
     * Erweitert die Vorschaubilder-Anzeige, so dass bei Klick die nächst
     * groessere Stufe angezeigt wird.
     */
    function enhanceThumbnails() {
        $('img.thumb').each(function(i, item){
            //console.log(i, item, this);
            var url_parts = $(item).attr('src').split('/');
            var filename = url_parts[(url_parts.length - 1)];
            var page = filename.split('.')[0];
            var height = url_parts[(url_parts.length - 2)];
            var attachment_id = url_parts[(url_parts.length - 3)];
            $(this).wrap('<a href="#"></a>');
            $(this).parent().click({
                attachment_id: attachment_id,
                height: height,
                index: (page - 1)
            }, zoomThumbsClick);
        });
    }

    OffenesKoeln.documentDetails(ok_document_url, function(data){
        //console.log(data);
        readThumbnailData(data);
        enhanceThumbnails();
    });

    truncateFulltext();
});
        

/*
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

*/


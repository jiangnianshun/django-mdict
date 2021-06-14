CKEDITOR.plugins.add( 'mruby', {
    icons: 'mruby',
    init: function( editor ) {
        editor.addCommand( 'insertmruby', {
            exec: function( editor ) {
                var text=editor.getSelection().getNative().toString();
                var item_group=text.split(/[\]」]/g);
                var html_str="";

                item_group.forEach(function(item){
                    if(item!=""){
                        var lmark = item.indexOf('[');
                        if(lmark<0){
                            lmark = item.indexOf('「');
                        }
                        if(lmark<0){
                            html_str+=item;
                        }else{
                            var kanji=item.substring(0,lmark);
                            var kana=item.substring(lmark+1);
                            var rubyText="<ruby><rb>"+kanji+"</rb><rt>"+kana+"</rt><rp>("+kana+")</rp></ruby>";
                            html_str+=rubyText;
                        }
                    }
                })

                editor.insertHtml(html_str);
            }
        });
        editor.ui.addButton( 'mruby', {
            label: 'convert to ruby tag',
            command: 'insertmruby',
            toolbar: 'insert'
        });
    }
});
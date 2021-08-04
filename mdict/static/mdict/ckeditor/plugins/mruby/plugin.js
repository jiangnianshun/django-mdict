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
                        var ltype = 1;
                        if(lmark<0){
                            lmark = item.indexOf('「');
                            ltype = 2;
                        }
                        if(lmark<0){
                            html_str+=item;
                            if(ltype==1){html_str+="]"}else{html_str+="」"}
                        }else{
                            var kanji=item.substring(0,lmark);
                            var kana=item.substring(lmark+1);
                            if(kanji==""||kana==""||kanji==" "||kana==" "){
                                html_str+=item;
                                if(ltype==1){html_str+="]"}else{html_str+="」"}
                            }else{
                                var rubyText="<ruby><rb>"+kanji+"</rb><rt>"+kana+"</rt><rp>("+kana+")</rp></ruby>";
                                html_str+=rubyText;
                            }
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
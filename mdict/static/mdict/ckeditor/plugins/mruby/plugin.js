CKEDITOR.plugins.add( 'mbox', {
    icons: 'mbox',
    init: function( editor ) {
        editor.addCommand( 'insertmbox', {
            exec: function( editor ) {
                var text=editor.getSelection().getNative().toString();
                var html_str="<span style='border:1px solid black !important'>"+text+"</span> ";
                //末尾空格避免后面输入的文字也被加入span中
                editor.insertHtml(html_str);
            }
        });
        editor.ui.addButton( 'mbox', {
            label: 'insert box',
            command: 'insertmbox',
            toolbar: 'insert'
        });
    }
});
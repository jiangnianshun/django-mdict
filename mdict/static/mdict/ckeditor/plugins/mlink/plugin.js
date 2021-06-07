CKEDITOR.plugins.add( 'mlink', {
    icons: 'mlink',
    init: function( editor ) {
        editor.addCommand( 'insertmlink', {
            exec: function( editor ) {
                var text = editor.getSelection().getNative();
                editor.insertHtml( '[link]'+text+'[/link]' );
            }
        });
        editor.ui.addButton( 'mlink', {
            label: 'insert link',
            command: 'insertmlink',
            toolbar: 'insert'
        });
    }
});
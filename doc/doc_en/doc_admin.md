### admin operation

Enter the background admin interface

[http://127.0.0.1:18000/admin/](http://127.0.0.1:18000/admin/)

* return to home page
<br>In the admin, click View Site at the top of the page to return to the main page.

* MDICT/Mdict dictionary:
<br>No need to add dictionaries manually. Only used to modify dictionary name, dictionary sorting, and whether to enable the dictionary.

* MDICT/built-in entries:
<br>Add entries from the built-in dictionary, support images and rich text, and support LaTex formulas.

* LaTex formula insertion:
<br>Method 1. Click the latex formula button (button with the summation symbol) to insert the formula; <br />Method 2. Enter manually and wrap the formula with $.

* Custom command:
<br> [link]The target entry[/link]
<br> [wrap]The content to be folded[/wrap]
<br> Custom command insertion:
<br> 1. Select the text, click the L button, the text will be automatically wrapped with [link], and the selected text will be displayed as an entry jump. <br />2. Select the text, click the W button, the text will be automatically wrapped with [wrap], and the selected text will be folded.

* MDICT/Online Dictionary:
<br>Add an online dictionary and replace the characters to be queried in the URL with %WORD%. Some websites do not support displaying in iframes. In this case, you need to remove the check box for opening in iframes.

* MDICT/tag
<br>Create tags for built-in terms.

* MDICT/Dictionary Grouping
<br>Create a dictionary group and then add the dictionary to the group.

* Enable/disable all dictionaries
<br>On the Mdict dictionary page, check the box before the ID, select all dictionaries on the first page, click on the right side of the execute button to select all XXX Mdict dictionaries, select EnableAllDics/DisableAllDics in the action drop-down box, and finally click the execute button.
  
### Built-in dictionary

The built-in dictionary adds entries through the background admin, supports LaTex formulas (MathJax), supports rich text and inserted pictures (django-ckeditor), and supports exporting to txt in mdict format. Since the current dictionary software does not support MathJax, it will not work when exporting txt. Export MathJax.

Order:

[link]abc[/link]

Create a link to the abc entry

[wrap]content[/wrap]

The contents of the package will be collapsed and need to be clicked to expand.

Export the built-in dictionary:


```
python script/export_builtin_dic.py
```

The built-in dictionary is exported to django-mdict/export/, export.txt is the exported text, and data is the exported resource. Mathjax is not supported after export. The wrap script goldendict supports it, but mdict does not.
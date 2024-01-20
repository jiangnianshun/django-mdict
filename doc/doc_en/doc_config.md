### Settings

Most of the following functions require the next query to take effect, that is, re-query and generate the page after being enabled.

* The enter key of the keyboard is bound to the query button, and the up and down arrow keys are bound to expand the previous term and expand the next term buttons. You can directly press the up and down keys or press ctrl+up and down keys. Pressing the up and down keys directly will trigger the browser's own For scrolling, it is more convenient to press the right ctrl + up and down keys with one hand on the full keyboard.

* Forced refresh: The background will cache the recently queried content. In order to display changes in query results during debugging, forced refresh needs to be enabled, and the next query will take effect.

* Jump to new tab page: By default, clicking the entry:// connection will query on the current page. After checking this option, a new tab page will be opened for query, and the next query will take effect.

* Force the use of full Song Dynasty: Forcibly change the fonts of all iframes to full Song Dynasty, which will take effect in the next query.

* Expand multiple dictionaries at the same time: By default, only one dictionary will be expanded. After it is turned on, multiple dictionaries are allowed to be expanded at the same time. However, the buttons to jump to the previous and next entries are invalid at this time, and the next query will take effect.

* Enable text selection menu: After enabling this function, after selecting text in the dictionary, a menu will pop up with three buttons: copy, query the selected word on the current page, open a new tab page to query the selected word, and the next query will take effect.

* Block default click: The click event of the entry is canceled and the next query will take effect.

* New tab page search: Select text on the full-text search page and single dictionary query page, click the new window query, if the new tab page is opened, the new window will open the query page for query, otherwise the full-text search or single dictionary query page will be opened Make a query and the next query will take effect.

* Accurate height calculation: Calculate the height of each element in the iframe to obtain the total height. The expansion speed will be slightly slower. The purpose is to solve the problem of incorrect height acquisition caused by absolute positioning in some dictionaries. The next query will take effect.

* Fixed height: Set the height of the iframe to be fixed. In order to solve the problem of abnormal display at custom heights such as phet.zim, the precise calculation of the height will be invalid after it is turned on, and it will take effect on the next query.

* Save as default value: If the value is not saved as default value, the settings will be restored to default after the page is refreshed.

* Convert text to Simplified Chinese and Convert text to Traditional Chinese buttons: Convert the content of the currently expanded entry into Traditional Chinese and Simplified Chinese. Known issues: Due to using direct replacement conversion, the results are inaccurate and have unconverted words.

* Night mode and day mode buttons: switch between night mode and original mode. Known issue: The M-W Visual Dictionary dictionary folding and expanding operation is invalid in night mode because it performs full matching judgment on class.

* Random query button: Randomly query an entry.

* Online dictionary: The online dictionary is added in the background admin. Change the word queried in the URL to %WORD%. There are two modes, open in an iframe or open in a new tab (some websites do not support display in an iframe).

### Configuration file

django-mdict/config.ini

#### [COMMON]

cache_num: Query prompt cache number

search_cache_num: The number of query (paging) caches

builtin_dic_enable: enable built-in dictionary

es_host: elasticsearch startup url (including port)

open_path_enable: Whether to allow opening the local dictionary folder (only local access is valid)

ws_server_port: The port number to enable ws_server under windows (default value 8766, 8765 is the default port of anki connect)

index_id: Select the home page (currently only 1 and 2)
#### [SEARCH]

merge_entry_max_length: The default value is 1000. Entries with the same term are merged. When there are multiple query results in the same dictionary, entries with a length less than 1000 will be merged. If not merged at all, set to 0.

st_enable: Enable Traditional and Simplified conversion

chaizi_enable: Enable word splitting and reverse search

fh_char_enable: Enable full-width character conversion (convert full-width English to half-width English)

kana_enable: Enable kana conversion (hiragana and katakana conversion)

romaji_enable: Enable romaji kana conversion

force_refresh: Enable force refresh (when enabled, it will query again instead of reading from the cache)

select_btn_enable: Enable text selection menu (pop-up box after selecting text in the entry, only valid on PC)

disable_iframe_click: Block the default click event in iframe (turn off the automatic pronunciation of the dictionary and solve the problem of click accents, which will take effect on the next query)

history_enable: whether to save query history

suggestion_num: number of query suggestions

force_font: Force all entries to use Song Dynasty (effective for the next query)

card_show: Allows multiple entries to be expanded at the same time (effective for the next query)

default_group: default group

new_label_link: Open a new label page (when clicking the entry to jump, it will not jump to this page but will open a new tab page for query, and the next query will take effect)

compute_every_element: Calculate each element of the iframe to calculate the total height

fixed_height: All entries are displayed at a fixed height

copy_with_tag: include html tags and css styles when copying

magnifier_enable: Enable image magnifier

hide-bottom-bar: hide the bottom toolbar
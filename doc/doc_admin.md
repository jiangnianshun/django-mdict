### admin操作

进入后台admin界面

[http://127.0.0.1:18000/admin/](http://127.0.0.1:18000/admin/)

* 返回主页
<br />在admin中点击页面上方的查看站点返回主页面。

* MDICT/Mdict词典：
<br />不需要手动添加词典。仅用于修改词典名，词典排序，是否启用词典。

* MDICT/内置词条：
<br />添加内置词典的词条，支持图片和富文本，支持LaTex公式。

* LaTex公式插入：
<br />方法1.单击latex公式按钮(求和符号的按钮)插入公式；
<br />方法2.手动输入，将公式用$包裹。

* 自定义命令：
<br />[link]要跳转的词条名[/link]
<br />[wrap]要折叠的内容[/wrap]
<br />自定义命令插入：
<br />1.选中文字，单击L按钮，自动将文字用[link]包裹，选中的文字显示为entry词条跳转。
<br />2.选中文字，单击W按钮，自动将文字用[wrap]包裹，选中的文字被折叠。

* MDICT/在线词典：
<br />添加在线词典，将url中要查询的字符用%WORD%替换，有些网站不支持在iframe中显示，此时需要去掉在iframe中打开的勾选。

* MDICT/标签
<br />创建标签，标签用于内置词条。

* MDICT/词典分组
<br />创建词典分组，然后将词典加入分组。

* 启用/停用所有词典
<br />Mdict词典页面，勾选ID前的复选框，选择第一页所有的词典，点击执行按钮右边的选中所有的XXX个Mdict词典，选择动作下拉框中的EnableAllDics/DisableAllDics，最后点击执行按钮。
  
### 内置词典

内置词典通过后台admin添加词条，支持LaTex公式（MathJax），支持富文本和插入图片（django-ckeditor），支持导出为mdict格式的txt，由于目前词典软件不支持MathJax，因此导出txt时不会导出MathJax。

命令：

[link]abc[/link]

创建一个跳转到abc词条的连接

[wrap]内容[/wrap]

包裹的内容会被折叠，需要点击展开。

导出内置词典：

```
python export_builtin_dic.py
```

内置词典导出到django-mdict/export/，export.txt是导出的文本，data是导出的资源，导出后不支持mathjax，wrap脚本goldendict支持，mdict不支持。
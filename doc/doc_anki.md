1. 安装电脑版anki，安装插件anki-connect（插件代码：2055492159），重启anki。

anki-connect：[https://github.com/FooSoft/anki-connect](https://github.com/FooSoft/anki-connect)

2. 保持anki在后台运行，查此页面底部按钮栏会出现添加卡片按钮。将内容复制到卡片正面和背面，然后选择牌组然后单击添加卡片到按钮创建卡片。

卡片正面只能粘贴为纯文本，卡片背面可以选择粘贴为纯文本或带样式文本。

自动复制：自动将当前展开词条的词头无样式复制到卡片正面，将当前展开词条的内容带样式复制到卡片背面。
复制时词条中有未展开的内容，复制后将无法展开。如果HTML结构较复杂，复制耗时会很长。

带样式复制会丢失部分样式。且仅能显示在线图片，不支持图片和音频的插入，anki不支持base64图片的显示。不支持ckeditor5的浏览器中无法使用（cefpython无法使用）。

![图片](img/img080901.png?raw=true)
划词脚本工具仅适用于win10，cefpython3的python版本最高支持为3.9。

1. 安装依赖。

```
pip install -r requirements3.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. 将django-mdict/huaci/huaci.pyw发送到桌面快捷方式。

3. 双击运行，右下角出现托盘图标。

4. 默认url是http://127.0.0.1:8000/mdict/?query=%WORD%，在huaci/utils/huaci.ini中修改url。

如果查词结果是空白，查看huaci/utils/huaci.ini中的ip和端口是否正确。

5. 选择文字，按ctrl+c+c快捷键开始查询。

6. 在托盘图标上右键退出，关闭划词工具。

如果需要用OCR查词，需要安装tesseract。

1. 下载安装tesseract-OCR.exe，并将tesseract.exe的路径添加到系统的环境变量Path中。

2. 打开划词工具的设置界面，选择OCR查词。按ctrl+c+c，鼠标点击两次，框选OCR的范围。

如果划词工具出现问题，尝试删除huaci/huaci.cache缓存文件夹。

页面缩放比例，设置huaci/utils/huaci.ini中auto_zooming，-1.0是75%;0.0是100%;1.0是125%;2.0是150%。
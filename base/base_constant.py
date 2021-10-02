import re

reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t|《》（）？！，。“”‘’：；]'
regp = re.compile(reg)

builtin_dic_prefix = '''
<link rel='stylesheet' href='/static/bootstrap/css/bootstrap.min.css'>
<link rel='stylesheet' href='/static/mdict/css/mdict.css'>
<style>
    table,th,td{border-width:1px !important;border-collapse:separate !important;}
</style>
<script>
    MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
      }
    };
</script>
<script id="MathJax-script" async src="/static/mdict/mathjax/3.1.2/tex-chtml-full.js"></script>
'''

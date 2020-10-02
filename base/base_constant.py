builtin_dic_prefix = '''
<link rel='stylesheet' href='/static/bootstrap-4.4.1/css/bootstrap.min.css'>
<link rel='stylesheet' href='/static/mdict/css/mdict.css'>
<script>
    //启用mathjax的行内模式
    MathJax = {
      tex: {
        inlineMath: [['$', '$']]
      }
    };
    function elementDisplay(objname){
        var obj=document.getElementsByName(objname);
        for(var i=0;i<obj.length;i++){
            if(obj[i].style.display !='none'){
                obj[i].style.display='none';
            }else{
                obj[i].style.display='block';
            }
        }
    }
</script>
<script id="MathJax-script" async src="/static/mdict/MathJax-master/es5/tex-chtml-full.js"></script>
'''

function create_new_url(entry,group){
    var url = window.location.href;
    var qn=url.indexOf('?query')
    if(qn>-1){
        var url=url.substring(0,qn);
    }
    qn=url.indexOf('&query')
    if(qn>-1){
        var url=url.substring(0,qn);
    }

    if(url.indexOf('?')>-1){
        url=url+'&query='+entry;
    }else{
        url=url+'?query='+entry;
    }

    url=url+'&group='+group;

    return url;
}

function is_index(){
    var dic_pk=$("html").attr("data-dic-pk");
    if(typeof(dic_pk)=="undefined"||dic_pk==-1){//index.html
        return true
    }else{//dic.html
        return false
    }
}

function get_url_param(name){//待处理
    var url_string = window.location.href;
    var url = new URL(url_string);
    return url.searchParams.get(name);
}

function change_title_and_url(query){
    document.title=query;//修改标题
    var group_name=$('#dic-group').val();
    var default_group=$('#dic-group').find('option:contains('+group_name+')').attr('data-pk');
    var url=create_new_url(query,default_group);

    var title=query+':'+default_group;
    window.history.pushState({'query':query,'group':default_group},title,url);
    //window.history.replaceState({'title':title},title,url);
    //修改url，但不刷新页面，第一个参数可以传空数组，第二个参数可以传空字符串。
}

function show_first_card(){
	//展开第一个词典
    var target="#card-element-0";
    //var card="div[id^=card-element-]";

	if($(target).length>0){
		$(target).collapse('show');
		//show是展开，hide是折叠
	}
}

function close_autocomplete(form){
	$(form).children("input").autocomplete("close");//按下enter键时关闭autocomplete下拉框
	document.activeElement.blur();//收回手机浏览器的软键盘
	return false;
}

function thousands(num){
        var str = num.toString();
        var reg = str.indexOf(".") > -1 ? /(\d)(?=(\d{3})+\.)/g : /(\d)(?=(?:\d{3})+$)/g;
        return str.replace(reg,"$1,");
}

function html_escape(text,all){
	//后端用urllib.parse.quote转义，汉字和符号都会被转义。
	//标题只需要转义影响html元素的符号。
	if(text==null){
		return "";
	}else if(all){
        return encodeURIComponent(text).replace(/[!'()*]/g, escape);
	}else{
        //返回字符实体
        return text.replace(/[<>'"&]/g, function(match, pos, originalText){
		switch(match){
			case "'":return "&apos;";
			case "<":return "&lt;";
			case ">":return "&gt;";
			case "&":return "&amp;";
			case "\"":return "&quot;";
		}
		});
	}
}

function html_unescape(text){
    if(text==null){
		return "";
	}else{
        return decodeURIComponent(text);
	}
}

function forbid_contextmenu(){
	//禁止手机浏览器的上下文菜单
	if(!is_PC()){
        window.addEventListener("contextmenu", function(e) {
            e.preventDefault();
            create_tooltip(e);
        })
    }
}

function is_PC() {
    var userAgentInfo = navigator.userAgent;
    var Agents = ["Android", "iPhone",
                "SymbianOS", "Windows Phone",
                "iPad", "iPod", "Mobile"];
    var flag = true;
    for (var v = 0; v < Agents.length; v++) {
        if (userAgentInfo.indexOf(Agents[v]) > 0) {
            flag = false;
            break;
        }
    }
    return flag;
}


function clear_parent_card(container){
	var card=container.children(".card");
	if(card.length>0){card.remove();}
}

function clear_card(){
	var card=$(".card");
	var d=$("#no-found");
	if(card.length>0){card.remove();}
	if(d.length>0){d.remove();}
}
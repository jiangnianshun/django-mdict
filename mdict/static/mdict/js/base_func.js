function create_new_url(entry){
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
    var url=create_new_url(query);
    window.history.pushState({},'',url);//修改url，但不刷新页面。
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

function set_iframe_height(iframe) {
    if (iframe) {
		var iframeWin;
		if(iframe.contentWindow){
			iframeWin = iframe.contentWindow;
			if (iframeWin.document.body) {
				iframe.height = iframeWin.document.body.scrollHeight;
			}
		}else if(iframe.contentDocument){
			iframeWin = iframe.contentDocument.parentWindow;
			if (iframeWin.document.body) {
				iframe.height = iframeWin.document.body.scrollHeight;
			}
		}

    }
}

//在正文中已用插件代替
//但是插件对.modal-content中的iframe不生效，因此还用这个调节高度。
function resize_iframe_height(){
	$("#modal-container-brief iframe").each(function (index) {//设置iframe高度为内容高度
	//这个方法设置的SimpleWiki20140116的car词条也是多出一块空白
		var that = $(this);

		(function () {
			setInterval(function () {
				set_iframe_height(that[0])
			}, 500)
		})(that)
	});

}

function thousands(num){
        var str = num.toString();
        var reg = str.indexOf(".") > -1 ? /(\d)(?=(\d{3})+\.)/g : /(\d)(?=(?:\d{3})+$)/g;
        return str.replace(reg,"$1,");
}

function space_escape(text){//img的src里的空格必须转义
	if(text==null){
		return "";
	}else{
		return text.replace(/[ ]/g, "%20");
	}
}

function html_escape(text){
	if(text==null){
		return "";
	}else{
		return text.replace(/[<>'"&]/g, function(match, pos, originalText){
		switch(match){
			case "'":return "&#39;";
			case "<":return "&lt;";
			case ">":return "&gt;";
			case "&":return "&amp;";
			case "\"":return "&quot;";
		}
		});
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
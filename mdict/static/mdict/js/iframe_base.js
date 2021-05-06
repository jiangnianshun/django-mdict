var t_img; // 定时器
var isLoad = true; // 控制变量

// 判断图片加载的函数
function isImgLoad(callback){
    // 查找所有图，迭代处理
    $('img').each(function(){
        // 找到为0就将isLoad设为false，并退出each
        if(this.height === 0){
            isLoad = false;
            return false;
        }
    });

    callback();//这里要调用一次，因为部署在云服务器上时，由于网络延迟，图片加载很慢。

    // 为true，没有发现为0的。加载完毕
    if(isLoad){
        clearTimeout(t_img); // 清除定时器
        // 回调函数
        //callback();
    // 为false，因为找到了没有加载完成的图，将调用定时器递归
    }else{
        isLoad = true;

        t_img = setTimeout(function(){
            isImgLoad(callback);
        },100); // 100毫秒扫描一次
    }
}

function copyToClip(content) {
    var aux = document.createElement("input");
    aux.setAttribute("value", content);
    document.body.appendChild(aux);
    aux.select();
    document.execCommand("copy");
    document.body.removeChild(aux);
}

function in_page_jump(ob,entry){//页内跳转
	//iFrame.contentWindow.location.href=entry;是在iframe中跳转，而window.location.href=entry;是在主页面进行跳转；
	//由于iframe高度是100%，因此这两种方法对锚点的跳转都无效。
	//ob锚点所在的元素，entry要跳转的锚点的名称

	var e=entry;
    var frame_element=window.frameElement
	if(frame_element==null){return;}
	var id=frame_element.id;
	var y=0;

	//计算滚动距离
	if(e=="top"){
		y = $("#"+id,parent.document).offset().top;
	}else{
		if(ob.parents("html").find('[name="'+entry+'"]').length>0){
		    y = $("#"+id,parent.document).offset().top + ob.parents("html").find('[name="'+entry+'"]').offset().top;
		}else if(ob.parents("html").find('[id="'+entry+'"]').length>0){
		    y = $("#"+id,parent.document).offset().top + ob.parents("html").find('[id="'+entry+'"]').offset().top;
		}

	}

	//进行滚动
	if(e=="top"||ob.parents("html").find('[name="'+entry+'"]').length>0||ob.parents("html").find('[id="'+entry+'"]').length>0){
		$(window.parent).scrollTop(y);
	}

	//清空in-page-jump标识
	$("#card-container",parent.document).attr("in-page-jump","");
}

function ihyperlink(e){
    var ob=$(this);
    query=ob.attr("href")||null;
    //href存储是要跳转的词条或要获取的图片和音频名，这里不能用this.href获取href的值，在firefox中正常，但在edge浏览器中，获取的href后会被自动加一个斜杠，导致最后查询失败。
    e.preventDefault();
    if(query!=null){
//		    e.preventDefault();
        if(query.indexOf("entry")==0){//处理entry超链接

            var entry=query.substring(8);
            if(entry[0]=="#"){
                //#锚点
                //页面内跳转到锚点
                in_page_jump(ob,entry.substring("1"));

            }else{
                //entry#锚点
                //跳转到entry词条的锚点位置
                var sharp=entry.indexOf("#");
                var inPageJump="";
                if(sharp!=-1){
                    inPageJump=entry.substring(sharp+1);
                    entry=entry.substring(0,sharp);
                }
                //自动查询超链接的entry
                var backslash=entry.indexOf("/");
                if(backslash==entry.length-1){
                    entry=entry.substring(0,backslash);
                }

                var new_label=$('#config-link-new-label',parent.document).prop("checked");
                if(new_label){
                    //通过url参数设置新页面的in-page-jump参数
                    var url=create_new_url(entry);

                    window.open(url);
                }else{
                    $('#query',parent.document).val(html_unescape(entry));
                    $("#card-container",parent.document).attr("in-page-jump",inPageJump);
                    $('#mdict-query',parent.document).trigger("click");
                }


            }
        }else if(query.indexOf("http")==0||query.indexOf("www.")==0){
            window.open(query);
        }else if(query.indexOf("sound")==0){//处理sound超链接，常见spx，mp3,wav格式
            var audio=query.substring(8);
            if(audio[0]!='/'&&audio[0]!='\\'){
                audio='/'+audio;
            }
            audio=html_escape(audio,true);

            var url=$('body').attr('data-pk')+'/'+audio;

            if(ob.children("audio").length==0){
                query_audio(ob,url,true,null);
            }else{
                ob.children("audio")[0].play();
            }
        }else if(query.indexOf("#")==0){
            in_page_jump(ob,query.substring("1"));
        }else{
            var mark=query.indexOf('.html');
            if(mark>0&&query.length==mark+5){
                //新标签页打开zim的非entry的html页面
                window.open(query);
            }
            //pdf文件和epub文件点击下载
            var mark=query.indexOf('.pdf');
            if(mark>0&&query.length==mark+4){
                var link = document.createElement('a');
                link.download = html_unescape(query);
                link.href = query;
                link.click();
            }
            var mark=query.indexOf('.epub');
            if(mark>0&&query.length==mark+5){
                var link = document.createElement('a');
                link.download = html_unescape(query);
                link.href = query;
                link.click();
            }
        }
    }

}

function init_hyperlink(){
    init_hyperlink_click();

	var inPageJump=$("#card-container",parent.document).attr("in-page-jump");
	if(inPageJump!=""){
		//页内跳转
		//如果inPageJump不为空，说明这是从之前的entry跳转过来的，需要继续跳转锚点
		var ob=$("a[name='"+inPageJump+"']")||$("a[id='"+inPageJump+"']");

		in_page_jump(ob,inPageJump);
	}
}

function init_hyperlink_click(){
    //$("a").click(ihyperlink);
    $("a[href$='.mp3'],a[href$='.spx'],a[href$='.wav'],a[href$='.ogg']").click(ihyperlink);
	$("body").on("click", "a", ihyperlink);
	//给动态增加的a添加click
    var disable_iframe_click=$('#config-disable-iframe-click',parent.document).prop("checked");

    if(disable_iframe_click){
        $("a[href$='.mp3'],a[href$='.spx'],a[href$='.wav'],a[href$='.ogg']").click(function(event) {
            //LDOCE5++ V 2-15会删掉sound://，必须从结尾匹配。
            event.stopImmediatePropagation();
            //这会导致on绑定的click无效，但是click的事件有效。
        });
        //LDOCE5++ V 2-15的js中有在线发音，导致在桌面chrome中重复发音，需要禁止a的点击事件。
    }
}

var select_words='';

function create_tooltip(e){
    //本来body设置的是mouseup生成tooltip，然后mousedown删除tooltip，里面的元素设置的是mousedown触发事件，
    //但是t_new_search a的跳转无效，可能是a的点击事件和上面的点击事件冲突？而要打开新标签，必须要用户点击跳转才可以，否则会被拦截。

    if($('#tooltip').length>0){
        $('#tooltip').remove();
    }

    var target_x=e.pageX;

    var target_y=e.pageY - 35;//设置tooltip显示在上方，因为在手机上选择后下方会出现两个控制原点，导致挡住tooltip。

    var window_width=window.innerWidth;

    if(target_x+190>window_width){
        target_x=target_x-(target_x+190-window_width);
    }

    if(e.pageY<=0||e.pageY<21){
        target_y=e.pageY+25;
    }


    var r="";
    if (document.selection) {
        r = document.selection.createRange().text;
    }else if (window.getSelection()) {
        r = window.getSelection();
    }


    if (r!= "") {
        select_words=r.toString();//这里select_words是全局变量，且赋值时要将r转化为字符串，因为第二次点击时选择的文字会消失，不保存的话获得的是空字符串。

        var dic_pk=$("html",parent.document).attr("data-dic-pk");
        var dic_name=$("html",parent.document).attr("data-dic-name");
        var is_page=false;
        if(typeof(dic_pk)=="undefined"){
            dic_pk=-1;
            is_page=true;
        }
        var href=window.location.href;
        var mark=href.indexOf('?');
        if(mark>-1){
            href=href.substring(0,mark-1);
        }

        var url=href+'?query='+select_words;

        if(dic_pk!=-1){
            url+='&dic_pk='+dic_pk;
        }
        //url+='&token='+ new Date().getTime();
        var new_label_link=$('#config-new-label-link',parent.document);
        if(new_label_link.length==0||new_label_link.prop("checked")){
            href=window.location.href;
            mark=href.indexOf('mdict');
            if(mark>-1){
                href=href.substring(0,mark);
            }

            url=href+'mdict?query='+select_words;
        }

        var t_copy="<span id='t_copy'><a href='javascript:'>复制</a></span>";
        var t_search="<span id='t_search'><a href='javascript:'>查询</a></span>";
        var t_new_search="<span id='t_new_search'><a href='"+url+"' target='_blank'>新窗口查询</a></span>";

        //tooltip的样式在style变量中设置
        if(is_page){
            var tooltip = "<div id='tooltip' class='mdict-tooltip'>"+t_copy+t_new_search+"</div>";
        }else{
            var tooltip = "<div id='tooltip' class='mdict-tooltip'>"+t_copy+t_search+t_new_search+"</div>";
        }
        $("body").append(tooltip);
        $("#tooltip").css({
            "top": target_y + "px",
            "left": target_x + "px",
            "position": "absolute"
        }).show("fast");


        $("#t_copy").click(function(e){
            //e.stopPropagation();
            //阻止冒泡，子元素的点击事件不会冒泡到父元素，即子元素点击事件触发后，父元素的点击事件不会触发。
            copyToClip(select_words);
            //window.getSelection().empty();
            //当用mouseup和mousedown设置事件时，需要代码取消选择，但设置click时，第二次click会自动取消选择。
        })

        $("#t_search").click(function(e){
            //e.stopPropagation();
            $('#query',parent.document).val(select_words);
            window.getSelection().empty();
            $('#mdict-query',parent.document).trigger("click");

        })

        $("#t_new_search a").click(function(){
            //e.stopPropagation();
            //var a=$(this).children('a');
            //a.href=url;
            //a.target='_blank';
            //a.mouseup(function(){

            //})



            window.getSelection().empty();
        })
    }

}


function init_tooltip(){
	//选择文字后的弹出框
    $("body").click(function (e) {//body加一个右键点击消除事件
		create_tooltip(e);
    }).mousedown(function(e){
	  if(e.which == 3){
			window.getSelection().empty();
			$('#tooltip').remove();

		    //这是右键单击事件
	  }else if(e.which == 1){
			   //这是左键单击事件
	  }else if(e.which == 2){
			   //这是鼠标中键事件
	  }
	})

}

function resize_iframe(){
    if ('parentIFrame' in window){
        window.parentIFrame.size($('html').outerHeight());
    }
}

function fix_chrome_bug(){
	var userAgent = navigator.userAgent;
		// 判断图片加载状况，加载完成后回调
		//在firefox中，主页面先设置iframe为最小高度，当iframe加载完所有资源后，css，img等，
		//iframeResizer.contentWindow向主页面发送iframe高度，这样的缺点时，当iframe中某个图片超时，要等很长时间，才能改变iframe高度。
		//在chrome中，iframe一加载，iframeResizer.contentWindow向主页面发送iframe高度,
		//这样的缺点是高度不包含图片高度，因此当图片加载完后，被遮挡。
		isImgLoad(function(){
			resize_iframe();
		});
}

function fix_img_delay_bug(){
    setTimeout(function(){
        //slangit词典yuge词条中包含了一个iframe，引用了youtube上的视频，由于墙导致不断超时重试，很长时间失败后才能获取外部iframe的正确高度
        //因此这里设置一段时间后无法加载的，window.stop()停止页面加载，然后触发重置外部iframe的高度
        window.stop();
    },1500);
}

function init_night_mode(){
    //第一次加载时，从主页面节点获取不到，加载样式失败，需要在iframe内加载。
    if($("#night-mode",parent.document).attr('data-value')=='yes'){
        $('*').not('img').addClass('dm-night');
        $('img').addClass('dm-night-img');
    }
}


function init_iframe(){
	init_hyperlink();
    var select_btn_enable=$('#config-select-btn-enable',parent.document);
	if(select_btn_enable.length==0||select_btn_enable.prop("checked")){
	    init_tooltip();
	}
	fix_chrome_bug();
	//fix_img_delay_bug();
	forbid_contextmenu();
	init_night_mode();
}

function transform_all_text(isFt){
    var txt=document.body.innerHTML;
    document.body.innerHTML=transformText(txt, isFt);
}
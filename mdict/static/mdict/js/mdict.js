//模板字符串
var script=`
<script src="/static/jquery/jquery.min.js"><\/script>
<script src='/static/mdict/iframe-resizer/js/iframeResizer.contentWindow.min.js'></script>
<script src="/static/mdict/js/transform.js"></script>
<script src="/static/mdict/js/base_func.js"></script>
<script src="/static/mdict/js/mdict_base.js"></script>
<script src="/static/mdict/js/iframe_base.js"></script>
<script src="/static/mdict/js/mdict.js"></script>
<script src="/static/mdict/js/init_iframe.js" defer></script>
`;

var search_history=new Array();

var style=`
<style>
html,body{
	padding:0;
	overflow-y:hidden;
}
.mdict-tooltip{
	background-color:gray !important;
	color:#EEEEEE !important;
	border-radius:5px !important;
	font-size:1.1em !important;
	z-index:999 !important;
}
.mdict-tooltip span{
	white-space:nowrap !important;
	margin:5px !important;
}
.mdict-tooltip span a{
	background-color:gray !important;
	text-decoration:none !important;
	color:#EEEEEE !important;
	font-style:normal !important;
}
mark{
    color:red !important;
}
</style>
<link href="/static/mdict/css/night.css" rel="stylesheet">
`
var style_img=`
<style>
img{
	max-width:100% !important;
}
/*这里如果设置全部元素强制max-width:100%，slangit.com中smh词条的svg会特别大。*/
</style>
`
var style_font=`
<style>
@font-face {
font-family: FSung-m;
src: url(/media/font/FSung-m.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-1;
src: url(/media/font/FSung-1.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-2-1;
src: url(/media/font/FSung-2-1.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-2-2;
src: url(/media/font/FSung-2-2.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-3;
src: url(/media/font/FSung-3.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-F-1;
src: url(/media/font/FSung-F-1.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-F-2;
src: url(/media/font/FSung-F-2.ttf);
font-display:swap;
}
*{font-family:Arial,FSung-p,FSung-m,FSung-1,FSung-2-1,FSung-2-2,FSung-3,FSung-F-1,FSung-F-2 !important;}
</style>
`

function create_card(s_id,mdx_pk,mdx_name,mdx_entry,mdx_record,mdx_extra){
    var s_parent='#card-container';
    if($('#config-card-show').prop('checked')){
        var card_ele=`
        <div class='card' id='card-${s_id}'>
            <div class='card-header'>
                <span class='badge badge-light text-dark'>${html_escape(mdx_entry,false)}</span>
                <span class='text-primary collapsed card-link' href='#card-element-${s_id}' data-bs-toggle='collapse' aria-expanded="false" aria-controls="#card-element-${s_id}">${html_escape(mdx_name,false)}</span>
                <div style='padding-left:50px;font-size:0.6rem;'>${mdx_extra}</div>
            </div>
            <div class='collapse' id='card-element-${s_id}'>
                <div class='card-body' id='card-body-${s_id}'>
                </div>
            </div>
        </div>
        `;
    }else{
        var card_ele=`
        <div class='card' id='card-${s_id}'>
            <div class='card-header'>
                <span class='badge badge-light text-dark'>${html_escape(mdx_entry,false)}</span>
                <span class='text-primary collapsed card-link' href='#card-element-${s_id}' data-bs-toggle='collapse' aria-expanded="false" aria-controls="#card-element-${s_id}">${html_escape(mdx_name,false)}</span>
                <div style='padding-left:50px;font-size:0.6rem;'>${mdx_extra}</div>
            </div>
            <div class='collapse' id='card-element-${s_id}' data-bs-parent='${s_parent}'>
                <div class='card-body' id='card-body-${s_id}'>
                </div>
            </div>
        </div>
        `;
    }


    /*
    由于mdx_entry可能包含<等字符导致显示出错，因此需要转义。
    data-toggle='collapse'操作是控制展开和折叠
    href='#card-element-"+i+"'操作目标是#card-element-"+i+"
    bootstrap5改为data-bs-toggle和data-bs-target
    collapse默认折叠
    collapse show默认展开

    data-parent='#card-container'
    bootstrap5改为data-bs-parent
    在card-container的子元素的所有可折叠元素，同一时间只能有一个展开。
    bs4可以对data-parent赋值空字符串，但是bs5不能对data-bs-parent赋值空字符串。
    */
    return card_ele;
}


function create_html(mdx_pk,mdx_name,mdx_record){
    var force_font=$('#config-force-font',parent.document).prop("checked");
    if(force_font){
        if(mdx_name=='内置词典'){
            var header=style+style_font+script;
        }else{
            var header=style+style_img+style_font+script;
        }
    }else{
        if(mdx_name=='内置词典'){
            var header=style+script;
        }else{
            var header=style+style_img+script;
        }
    }
    var html=`
    <!DOCTYPE HTML>
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="referrer" content="never">
            ${header}
        </head>
            <body data-pk="${mdx_pk}">
            ${mdx_record}
        </body>
    </html>
    `;

    return html;
}

function bind_card(iframe,html){
    var card_link=$(iframe).parents(".card").find(".card-link");
    var card=$(iframe).parents(".card");
    card.on('hidden.bs.collapse',function(){
        //card折叠时消除选择文字弹出框
        var tooltop=$(this).find('iframe').contents().find('#tooltip');
        if(tooltop.length>0){
            tooltop.remove();
        }
    });

    card.on('show.bs.collapse',function(){//当card展开时才加载iframe内容，避免手机上的卡顿。
        if($(iframe).attr('data-content-fill')!='true'){
            if(iframe.getAttribute("data-name")!="内置词典"){
                html=html.replace(/\\n/g,'<br />');
                //懶虫簡明英漢漢英詞典错误的使用\n换行，很少词典有这个问题，因此放在前端处理
                //内置词典的\n不能被替换，会导致mathjax的\nu,\neq等命令无效
            }

            iframe.contentWindow.document.open();
            iframe.contentWindow.document.write(html);
            iframe.contentWindow.document.close();

            if($("#night-mode").attr('data-value')=='yes'){
                var eles=$(iframe).contents().find('*');
                eles.not('img').addClass('dm-night');
                eles.find('img').addClass('dm-night-img');
            }

            $(iframe).contents().find('span[src]').each(function(){
                //朗文现代5查jarring,jarringly,结果是span,span的src是base64图片，浏览器中不显示，这里重新生成img标签。
                var new_img=$('<img>',{
                    src:$(this).attr('src')
                })
                $(this).after(new_img);
            });
        }else{
            if($("#night-mode").attr('data-value')=='yes'){
                $(iframe).contents().find('*').not('img').addClass('dm-night');
            }else{
                $(iframe).contents().find('*').removeClass('dm-night').removeClass('dm-night-img');;
            }
        }
    });

    card.on('shown.bs.collapse',function(){
        //shown.bs.collapse是collapse展开完成事件
        var iframe_content=$(iframe).contents();
        if($(iframe).attr('data-content-fill')!='true'){
            if(iframe_content.find('html').css('writing-mode')=='vertical-rl'||iframe_content.find('body').css('writing-mode')=='vertical-rl'){
                //处理日文从右往左的竖排排版
                iFrameResize({
                    log:false,
                    checkOrigin:false,
                    widthCalculationMethod:'documentElementOffset',
                    minHeight:550,
                    warningTimeout:0,
                    scrolling:true,
//							onInit: function(iframe_a){
//							},
//							onResized: function(messageData) {
//							},
                },iframe);
                iframe_content.find('html').css('overflow-y','visible');
                iframe_content.find('body').css('overflow-y','visible');
            }else{
                iFrameResize({
                    log:false,
                    checkOrigin:false,
                    heightCalculationMethod:'documentElementOffset',
                    warningTimeout:0,
                    scrolling:true,
//							onInit: function(iframe_a){
//							},
//							onResized: function(messageData) {
//							},
                },iframe);
            }
            $(iframe).attr('data-content-fill','true');
        }

        /*
        log:false不显示debug信息
        checkOrigin:false不对iframe的url进行检查
        heightCalculationMethod
        bodyOffset和bodyScroll不计算margin，都偏小
        max一是有闪烁问题，二是有的词条有很大一块空白
        documentElementScroll会有大块空白
        documentElementOffset的白边较小，且点击后能恢复,但是pdf2htmlex生成的页面无高度.
        lowestElement准确度最高，会遍历各元素，问题一性能消耗高，二有的词条，比如朗文5++的comet，
        每次点击iframe高度都增大，原因是有元素设置了height="100%"，
        或者设置了固定约束距底边的距离，position="fixed",bottom="45px"，导致高度获取出问题。
        card展开关闭一段时间后再展开，高度0，需要手动点击一下高度才恢复正常。
        resizeFrom:'child'设置当iframe变化时更新状态，默认是parent窗口变化时更新状态。
        在modal-mdict需要设置为child，否则不会显示。
        warningTimeout:0,抑制iframeresizer的警告信息
        第二个参数是iframe的dom对象，如果不设置，则对全部的iframe都生效。
        tolerance设置iframe前后相差多少px时重绘
        scrolling:true显示滚动条，然后用overflow-y:hidden;抑制竖向，只显示横向。
        */

        var d=$(document).scrollTop();
        var t=$(this).offset().top;
        var s=$(window).height();
        if($(".card").length>1){
            //d>t,//当card-body展开使得card-header跑到屏幕上方去，且length大于1时，跳转。
            //t>s当词条在屏幕下方时
            if(d>t||t+35>d+s){
                $(window).scrollTop(t);
            }
        }

        //正文高亮
        var highlight_content=$('#highlight-content').prop("checked");
        if(highlight_content){
            var query=$.trim($('#query').val());
            if(query!=''){
                var pattern=/[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t|《》（）？！，。“”‘’：；]/g;
                var tmp_query = query.split(pattern);
                //去符号
                for(var tmp of tmp_query){
                    if(tmp!=''){
                        var context = $(iframe).contents().find('body')[0];
                        var instance = new Mark(context);
                        if(/[a-zA-Z]+/.test(tmp)){
                            instance.mark(tmp);
                        }else{
                            tmp = [].filter.call(tmp,function(s,i,o){return o.indexOf(s)==i;}).join('');
                            //去重
                            for(var j=0;j<tmp.length;j++){
                                instance.mark(tmp[j]);
                            }
                        }
                    }
                }
            }
        }
    });

    card.find('.defaultscale').click(function(){
        var iframe_body=card.find('iframe').contents().find('body');
        if($(this).val()==''){
            $(this).val(parseInt(iframe_body.css('font-size')));
        }
        iframe_body.animate({ fontSize: $(this).val() });
    });
}

function add_iframes(data,container,need_clear,is_list){
	//need_clear，第一次需要清除card
	//is_list，query_mdict传进来的字典，query_record传进来的是列表
	if(data.length==0){
		var t="<div id='no-found'>未查询到！</div>";
		container.append(t);
		return [-1,-1]
	}else{
		if(is_list){
			var d=data;
		}else{
			var d=data['data'];
			var page_size=data['page_size'];
			var total_count=data['total_count'];
			var total_page=data['total_page'];
			
			var current_page=data['current_page'];
			var iframe_length=$('#card-container iframe').length;
		}

		var s_id = 0;
		
		for(var i=0;i<d.length;i++){
			var record=d[i];

			var mdx_name=record["mdx_name"];
			var mdx_entry=record["mdx_entry"];
			var mdx_record=record["mdx_record"];
			var mdx_pk=record["pk"];
			var mdx_extra=record["extra"];

			if(typeof(mdx_extra)=="undefined"){
			    mdx_extra="";
			}
			
			if(need_clear){
				s_id=i;
			}else{
				s_id=iframe_length+i;
				
			}

            var card_ele=create_card(s_id,mdx_pk,mdx_name,mdx_entry,mdx_record,mdx_extra)
            var html=create_html(mdx_pk,mdx_name,mdx_record);


			//script加到最后，因为enwikipart1查gucci，最后有未完成的注释<!--，导致script被注释掉。

			var iframe = document.createElement('iframe');
			//iframe.width="100%";
			//iframe.height="auto";
			iframe.id="iframe-"+s_id;
			iframe.setAttribute("data-name", mdx_name);
			//iframe.src = 'data:text/html;charset=utf-8,' + encodeURIComponent(html);
			//html中的#号会被截断，导致iframe读取不完整，因此要编码，而encodeURIComponent()会编码#号，但是encodeURI()不会编码，问题是使用encodeURIComponent()载入的子页面，css无法载入。
			
			var card_body_id="#card-body-"+s_id;
			var card_mdict_i=$(card_body_id);
			if(card_mdict_i.length>0){//清理同一时间的多次异步产生的多个重复词条
				card_mdict_i.children().remove();
			}else{
				container.append(card_ele);
			}
			$(card_body_id).append(iframe);

			if($("#night-mode").attr('data-value')=='yes'){
                container.addClass('dm-night');
                container.find('*').addClass('dm-night');
                container.find('.card-header').addClass('dm-night-border');
            }
			
			(function(iframe,html){//通过闭包来避免for循环事件绑定中的赋值问题
				bind_card(iframe,html);
			})(iframe,html);
		}
		return [current_page,total_page,d.length]
	}
	
}


function add_to_history(query,result_num){
    if(!(query in search_history)){//设置本页面查询历史，重复的查询不加入
        search_history[query]=result_num;
        var badge_class="badge bg-primary rounded-pill";
        var li_class="list-group-item list-group-item-action d-flex justify-content-between align-items-center";
        if($('.dm-night').length>0){
            badge_class+=" dm-night";
            li_class+=" dm-night";
        }
        var badge_h=$('<span>',{
            text:result_num,
            class:badge_class,
        });
        var li_h=$('<li>',{
            text:query,
            class:li_class,
        });
        badge_h.appendTo(li_h);
        li_h.appendTo('#search-history');
        li_h.click(function(){
            if(query!=$("#query").val()){
                $("#query").val(html_unescape(query));
                $("#mdict-query").trigger("click");
            }
            $("#modal-container-history").modal("hide");
        })

    }
}

function query_es(query,container,page,need_clear,is_over){
	var dic_group=$('#dic-group option:selected').attr('data-pk');
	var es_phrase=$('#es-filter-phrase').prop("checked");
	var es_entry=$('#es-filter-entry').prop("checked");
	var es_content=$('#es-filter-content').prop("checked");
	var es_and=$('#es-filter-and').prop("checked");

	var dic_pk=$("html").attr("data-dic-pk");

	var frag_num=$('#frag-num').val();
	var frag_size=$('#frag-size').val();
	if(frag_num==''){frag_num=3;}
	if(frag_size==''){frag_size=50;}

	if(!es_entry&&!es_content){
	    console.log('must select one search item')
	    return
	}

	var data={"query":query,"dic_group":dic_group,"result_page":page,"force_refresh":$('#config-force-refresh').prop('checked'),
	"es-phrase":es_phrase,"es-entry":es_entry,"es-content":es_content,"es-and":es_and,"frag_num":frag_num,"frag_size":frag_size,
	"dic_pk":dic_pk};
	$.ajax({
		url:"/mdict/essearch/",
		contentType:'json',
		type:'GET',
		data:data,
		success:function(data){
			if(need_clear){clear_card();}

			//每次按钮点击后清理掉已有的显示的词条
            page=add_iframes(data,container,need_clear,false);
			//page[0]是当前页码，page[1]是总页码

		    var s2=`
			<div id='next-page' class='card card-header m-auto'>
				<div class='m-auto' style='color:#007bff;hover:pointer;'>
					继续加载
				</div>
			</div>
			`;
			$('#card-container #next-page').remove();

			if(page[2]>0&&page[1]>page[0]){
                container.append(s2);

                $('#card-container #next-page').on('click',function(){
                    query_es(query,container,page[0]+1,false,true);
                })
			}

			is_over=true
//			if(page[0]<page[1]){
//				var next_page=page[0]+1;
//				var t_over=false
//				if(next_page==page[1]){
//					t_over=true
//				}
//				query_es(query,container,next_page,false,t_over);
//			}else if(page[0]==page[1]){
//				is_over=true
//			}
			if(need_clear){
				$("#query").autocomplete("close");
				//有时查询结果比搜索提示出现的快，此时autocomplete没有关闭，因此这里要关闭。
				if(!is_over){
					$("#result_num").text('');//清空上一次的结果数目
					$("#result_time").text('');
				}

			}

			if(is_over){
                var result_num=$("#card-container iframe").length;

				$("#result_num").text(result_num);
				var start_time=$("#result_time").attr("data-start-time");
				var isover=$("#result_time").attr("data-isover");
				var end_time=new Date().getTime();
				if(isover){
				    $("#result_time").attr("data-start-time",end_time);
				}

				var elapse_time=process_time(end_time-start_time);

				$("#result_time").text(elapse_time);

				add_to_history(query,result_num);
			}
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function query_mdict(query,container,page,need_clear,is_over){
	var dic_group=$('#dic-group option:selected').attr('data-pk');

	var force_refresh=$('#config-force-refresh').prop('checked');
	var fh_char_enable=$('#config-fh-char-enable').prop("checked");
    var st_enable=$('#config-st-enable').prop("checked");
    var chaizi_enable=$('#config-chaizi-enable').prop("checked");
    var kana_enable=$('#config-kana-enable').prop("checked");

	var data={"query":query,"dic_group":dic_group,"page":page,"force_refresh":force_refresh,"fh_char_enable":fh_char_enable,"st_enable":st_enable,
    "chaizi_enable":chaizi_enable,"kana_enable":kana_enable};
	$.ajax({
		url:"/api/mdict2/mdict/",
		contentType:'json',
		type:'GET',
		data:data,
		success:function(data){
			if(need_clear){clear_card();}

			//每次按钮点击后清理掉已有的显示的词条
            page=add_iframes(data,container,need_clear,false);
			//page[0]是当前页码，page[1]是总页码
			if(page[0]<page[1]){
				var next_page=page[0]+1;
				var t_over=false
				if(next_page==page[1]){
					t_over=true
				}
				query_mdict(query,container,next_page,false,t_over);
			}else if(page[0]==page[1]){
				is_over=true
			}
			if(need_clear){	
				$("#query").autocomplete("close");
				//有时查询结果比搜索提示出现的快，此时autocomplete没有关闭，因此这里要关闭。
				if(!is_over){
					$("#result_num").text('');//清空上一次的结果数目
					$("#result_time").text('');
				}
				show_first_card();
			}

			if(is_over){
                online_search(query,container)

                var result_num=$("#card-container iframe").length;

				$("#result_num").text(result_num);
				var start_time=$("#result_time").attr("data-start-time");
				var isover=$("#result_time").attr("data-isover");
				var end_time=new Date().getTime();
				if(isover){
				    $("#result_time").attr("data-start-time",end_time);
				}

				var elapse_time=process_time(end_time-start_time);

				$("#result_time").text(elapse_time);

				add_to_history(query,result_num);
			}
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

//online_dic变量见mdict_base.js

function online_search(query,container){//有道在线
    var temp_online_dicts=[];
    var i=0;
    //这里可以和在online_dic初始化那里的代码整合
    $("#online-mdict-checkbox input:checked").each(function(){
        var item=$(this);
        var s_id=$('#card-container iframe').length+i;
        var mdx_name=item.val();
        var mdx_isiframe=$.parseJSON(item.attr("data-isiframe"));
        var mdx_entry=query;
        i+=1;
        //display:none不显示且不占位置，visibility:hidden;不显示且占位置
        if(mdx_isiframe){
            var s=`
            <div class='card' style='display:none;'>
                <div class='card-header'>
                    <span class='text-primary card-link collapsed' data-bs-target='#card-element-${s_id}' data-bs-toggle='collapse' >
                    <span class='badge badge-light text-dark'>${html_escape(mdx_entry,false)}</span>${html_escape(mdx_name,false)}</span>
                </div>
                <div class='collapse' id='card-element-${s_id}' data-bs-parent='#card-container'>
                    <div class='card-body' id='card-body-${s_id}'>
                    </div>
                </div>
            </div>
            `;

            var iframe = document.createElement('iframe');
            iframe.src=item.attr("data-url").replace('%WORD%',query);
            iframe.id="iframe-"+s_id;
            iframe.height='1000px';

            var card_body_id="#card-body-"+s_id;
            var card_mdict_i=$(card_body_id);
            if(card_mdict_i.length>0){//清理同一时间的多次异步产生的多个重复词条
                card_mdict_i.children().remove();
            }else{
                container.append(s);
            }

            $(card_body_id).append(iframe);

            (function(iframe){
                var card=$(iframe).parents(".card");
                iframe.onload=function(){
                    card.css('display','block');//未加载完是隐藏的，加载完后显示

                    //var script = document.getElementById(iframe.id).contentWindow.document.createElement('script');
                    //script.src='/static/mdict/iframe-resizer/js/iframeResizer.contentWindow.min.js';
                    //跨域，无法获取iframe的document，也无法插入js
                }
            })(iframe)
        }else{
            var s=`
            <div class='card'>
                <div class='card-header'>
                    <span class='text-primary card-link collapsed' id='card-new-${s_id}' href='javascript:void(0);'>
                    <span class='badge badge-light text-dark'>${html_escape(mdx_entry,false)}</span>${html_escape(mdx_name,false)}</span>
                </div>
            </div>
            `;

            container.append(s);

            var card_new_id="#card-new-"+s_id;

            $(card_new_id).click(function(){
                var url=item.attr("data-url").replace('%WORD%',query);
                //window.open(url,"_blank")
                window.open(url, "Newwindow", "height=1000, width=1000, top=100, left=100, scrollbars=yes, resizable=yes");
            });
        }
    });
    show_first_card();

}

function process_time(time){
	if(time<1000){
		return time+'ms';
	}else{
		return time/1000+'s';
	}
}


function decodeSpeex(file) {
	var ogg = new Ogg(file, {file: true});
	ogg.demux();

	var header = Speex.parseHeader(ogg.frames[0]);
    if(header.nb_channels==2){
        header.rate=header.rate/2;
        //播放牛8简的spx是正常的，mode=1,nb_channels=1,rate=16000，
        //播放NHK日本語発音アクセント辞書的spx，特别快，mode=2,nb_channels=2,rate=32000，如果设置rate为16000就正常了
        //日语发音库，mode=2,nb_channels=1,rate=32000，正常
        //推测可能和nb_channels有关。
    }

	var comment = new SpeexComment(ogg.frames[1]);

	var spx = new Speex({
		quality: 8,
		mode: header.mode,
		rate: header.rate
	});

	var waveData = PCMData.encode({
		sampleRate: header.rate,
		channelCount: header.nb_channels,
		bytesPerSample: 2,
		data: spx.decode(ogg.bitstream(), ogg.segments)
	});

	return new Blob([Speex.util.str2ab(waveData)], {type: "audio/wav"});
}


function play_speex(ob,array,play,mime,func){
    var data = new Uint8Array( array );
    $.when(//动态加载js
        $.getScript("/static/mdict/js/bitstring.min.js"),
        $.getScript("/static/mdict/js/pcmdata.min.js"),
        $.getScript("/static/mdict/js/speex.min.js"),
        $.Deferred(function( deferred ){
            $( deferred.resolve );
        })
    ).done(function(){
        blob = decodeSpeex(String.fromCharCode.apply(null, data));
        if(blob!=null&&blob!=""){
            if(typeof(func)=='function'){
               func(true);
            }
            if(ob.children("audio").length>0){
                ob.children('audio').remove();
            }

            ob.append(new Audio(URL.createObjectURL(blob)));

            if(play){
                ob.children("audio")[0].play();
            }
        }else{
            if(typeof(func)=='function'){
                func(false);
            }
        }
    });
}

function play_audio(ob,array,play,mime,func){
    blob= new Blob([array],{type:mime});
    if(blob!=null&&blob!=""){
        if(typeof(func)=='function'){
            func(true);
        }
        if(ob.children("audio").length>0){
            ob.children('audio').remove();
        }

        ob.append(new Audio(URL.createObjectURL(blob)));

        if(play){
            ob.children("audio")[0].play();
        }
    }else{
        if(typeof(func)=='function'){
            func(false);
        }
    }
}

function query_audio(ob,url,play,func){
	var xhr = new XMLHttpRequest();
	xhr.open('GET', url, true);
	xhr.responseType = 'arraybuffer';
	 
	xhr.onload = function(e) {
	  if (this.status == 200) {
		var mime='';
		var blob=null;
		var mime=this.getResponseHeader('content-type');
		var array=this.response;

		if(mime=='audio/speex'){
			play_speex(ob,array,play,mime,func);
		}else if(mime=='audio/wav'||mime=='audio/mp3'||mime=='audio/mpeg'||mime=='audio/ogg'){
			play_audio(ob,array,play,mime,func);
		}else{
		    if(typeof(func)=='function'){
                func(false);
            }
		}
	  }
	};
	 
	xhr.send();
}


function query_key(container,entry){
	var dic_pk=$("html").attr("data-dic-pk");
	var data={"entry":entry,"dic_pk":dic_pk};
	$.ajax({
		url:"/mdict/key/",
		contentType:'json',
		type:'GET',
		data:data,
		success:function(data){
			var d=$.parseJSON(data);
            var s=d["start"];
			var e=d["end"];
			var p1=d["p1"];
			var p2=d["p2"];
			var new_entry=d["entry"];
			if(s!=-1){
				$("#alert-box").empty();
				query_scroll(p1,p2,dic_entry_nums,0);
				query_record(container,new_entry,dic_pk,s,e);
			}else{
				var alert_box=`
				<div class="alert alert-danger alert-dismissable">
					<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
					未查询到${entry}，无法跳转！
				</div>
				`;
				$("#alert-box").empty();
				$("#alert-box").append(alert_box);
			}
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function query_record(container,entry,dic_pk,start,end){
    if(end==0){end=-1;}//-1存储后变为0
	var data={"entry":entry,"dic_pk":dic_pk,"start":start,"end":end};
	$.ajax({
		url:"/mdict/record/",
		contentType:'json',
		type:'GET',
		data:data,
		success:function(data){
			var d=$.parseJSON(data);
			clear_card();
			clear_parent_card(container);
			//query_record在iframe外调用一次，在iframe内调用一次，因此这里用两个清除函数。;
            add_iframes(d,container,true,true);
			show_first_card();
            change_title_and_url(entry);
            add_to_history(entry,1);
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function query_scroll(p1,p2,num,direction){
    var dic_pk=$("html").attr("data-dic-pk");
	var data={"p1":p1,"p2":p2,"num":num,"direction":direction,"dic_pk":dic_pk};
	$.ajax({
		url:"/mdict/allentrys/",
		contentType:'json',
		type:'GET',
		data:data,
		success:function(data){
		var d=$.parseJSON(data);
		var data_list=d["entry_list"];
		var r_s_p1=d["s_p1"];
		var r_s_p2=d["s_p2"];
		var r_e_p1=d["e_p1"];
		var r_e_p2=d["e_p2"];
		
		var data_len=data_list.length;
		
		if(data_len>0){
			set_scroll(data_list,direction,func);

			$("#display_list").attr("data-start-p1",r_s_p1);
			$("#display_list").attr("data-start-p2",r_s_p2);
			$("#display_list").attr("data-end-p1",r_e_p1);
			$("#display_list").attr("data-end-p2",r_e_p2);
			if(dic_first){
				$("#li-0").trigger("click");//展开第一项
				dic_first=false;
			}else{
                scroll_display_list();
			}
		}
		
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function set_mdict_enable(obj){
    var data={"mdict_pk":$(obj).attr("data-pk"),"mdict_enable":$(obj).prop("checked")};
    $.ajax({
		url:"/mdict/mdictenable/",
		contentType:'json',
		type:'GET',
		data:data,
		success:function(data){
            console.log(data);
		},
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function set_all_mdict_enable(obj){
    var dic_list=new Array();
    var dic_tmp_list=new Array();
    var o_check = $(obj).prop("checked");

    $("#mdict-list-content .card-header input").each(function(){
        var t_check = $(this).prop("checked");
        if(t_check!=o_check){
            $(this).prop("checked", $(obj).prop("checked"));
            dic_tmp_list.push($(this).attr("data-pk"));
            //$(this).change();
        }

    })

    for(var i=0;i<dic_tmp_list.length;i=i+300){
        dic_list[i]=new Array();
        for(var j=i;j<i+300;j++){
            if(j>=dic_tmp_list.length)break;
            dic_list[i].push(dic_tmp_list[j])
        }
    }

    for(var i=0;i<dic_list.length;i++){
        set_all_mdict_ajax(dic_list[i],o_check)
    }
}

function set_all_mdict_ajax(dic_list,o_check){
    data={'dic_list':dic_list,"mdict_enable":o_check};
    $.ajax({
		url:"/mdict/mdictenable/",
		contentType:'json',
		type:'GET',
		traditional: true,
		data:data,
		success:function(data){
            console.log(data);
		},
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function get_mdict_list(container, es_icon_enable, es_page_enable){//载入词典列表
	$.ajax({
		url:"/mdict/mdictlist/",
		contentType:'json',
		type:'GET',
		success:function(data){
			var d=$.parseJSON(data);
			$("#dic_num").text(d.length);
			for(var i=0;i<d.length;i++){
				var dic_name=d[i]["dic_name"];
				var dic_file=d[i]["dic_file"];
				var dic_icon=d[i]["dic_icon"];
				var dic_pror=d[i]["dic_pror"];
				var dic_pk=d[i]["dic_pk"];
				var dic_enable=d[i]["dic_enable"];
				var dic_es_enable=d[i]["dic_es_enable"]


				var checked="";

				if(dic_enable){checked="checked";}

				if(dic_es_enable){
				    var es_icon="<i class='bi bi-check' style='color:green;'></i>"
				}else{
				    var es_icon="<i class='bi bi-x' style='color:red;'></i>"
				}

				es_icon+="<i class='bi bi-question index-status' style='color:gray;' data-pk="+dic_pk+"></i>"

				var checkbox_html=`
                            <div class="form-checkbox" style="display:inline;">
                                <input class="form-check-input" type="checkbox" id="customControlInline${i}" ${checked} data-pk=${dic_pk} onchange="set_mdict_enable(this)">
                                <label class="form-check-label" for="customControlInline${i}" style="display:inline;vertical-align:middle;"></label>
                            </div>
                            `
                if(!es_icon_enable){
				    es_icon="";
				}
				if(es_page_enable){
				    es_page='esdic'
				}else{
				    es_page='dic'
				}
                var s=`
                <div class="card-header">${checkbox_html}${es_icon}
                    <img class="dic-icon" src="${html_escape(dic_icon,false)}"></img>
                    <span class="badge badge-light text-dark">${dic_pror}</span>
                    <a class="mdict-list-mark" href="/mdict/${es_page}/?dic_pk=${dic_pk}" data-file=${html_escape(dic_file)}>
                        ${html_escape(dic_name)}
                    </a>
                </div>
                `

				container.append(s);
			}

			var dic_pk=$("html").attr("data-dic-pk");
			if(dic_pk==-2){
                get_index_status();
		    }else{
		        if(dic_pk>0&&$("#scroll_list").length==0){
		            get_index_status();
		        }
		    }
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function get_index_status(){
    $.ajax({
		url:"/mdict/indexstatus/",
		contentType:'json',
		type:'GET',
		success:function(data){
			if(typeof(data)=='undefined'||data.indexOf('ConnectionError')>-1){
			    $("#live-toast-body").text("error:"+data);
                new bootstrap.Toast($("#live-toast")[0]).show();
                console.log("error:",data);
                $('#mdict-list-content .index-status').each(function(){
                    $(this).removeClass('bi-question');
                    $(this).removeClass('bi-moon-fill');
                    $(this).removeClass('bi-sun-fill');
                    $(this).removeClass('bi-x');
                    $(this).addClass('bi-cloud-slash');
                    $(this).css('color','gray');
                });
			}else{
                var st_data=$.parseJSON(data);
                var st_status = st_data['status'];
                var st_error = st_data['error'];
                if(st_error==''){
                    $('#mdict-list-content .index-status').each(function(){
                        var dic_pk = $(this).attr('data-pk');
                        if(st_status.hasOwnProperty(dic_pk)){
                            var index_status=st_status[dic_pk];

                            $(this).removeClass('bi-question');
                            $(this).removeClass('bi-moon-fill');
                            $(this).removeClass('bi-sun-fill');
                            $(this).removeClass('bi-x');
                            if(index_status==1){
                                $(this).addClass('bi-sun-fill');
                                $(this).css('color','green');
                            }else if(index_status==0){
                                $(this).addClass('bi-moon-fill');
                                $(this).css('color','orange');
                            }else{
                                $(this).addClass('bi-x');
                                $(this).css('color','red');
                            }
                        }
                    });
                }else{
                    $("#live-toast-body").text("error:"+st_error);
                    new bootstrap.Toast($("#live-toast")[0]).show();
                    console.log("error:",st_error);
                }
			}

		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function get_header(container){
	var data={"dic_pk":$("html").attr("data-dic-pk")};
	$.ajax({
		url:"/mdict/header/",
		contentType:'json',
		data:data,
		type:'GET',
		success:function(data){
			var d=$.parseJSON(data);
			var header=d['header'];
			var num=d['num_entrys'];
			var mdx_path=d['mdx_path'];
			var mdd_path=d['mdd_path'];
			
			var h_line="<div style='width:100%;height:1px;border:0;margin-top:1em;margin-bottom:1em;background-color:gray;'></div>";
			var title="";
			var description="";
			var num_entrys="词条数量："+thousands(num);
			var other_attributes="";
			for(var key in header){
				if(key!="StyleSheet"&&header[key].length>0){//不显示StyleSheet属性和空属性
					if(key=="Title"){
						if(header[key]!=''){
						    title=`<div style="font-size:22px;color:brown;">${header[key]}</div>`;
						}
					}else if(key=="Description"){
						if(header[key]!=''){
						    description=`<div>${header[key]}</div>`;
						}
					}else{
						other_attributes+=`<div>${key}：${header[key]}</div>`;
					}
					
				}
			}

			var file_info=`<div>${mdx_path}</div><div>${mdd_path}</div>`

//			description=description.replace('height="100%"','').replace("heigth='100%'",'');
			
			var style="<style>html,body{margin:0;padding:0;}img{max-width:100%;}</style>";

			if(title==''){
			    var html=style;
			}else{
			    var html=style+title;
			}

			if(description==''){
			    html+=h_line+num_entrys;
			}else{
			    html+=h_line+num_entrys+h_line+description;
			}
			html+=h_line+file_info+h_line+other_attributes+script;
			
			var iframe = document.createElement('iframe');
			iframe.width="100%";
			iframe.height="100%";
			iframe.id="dic-header";
			iframe.scrolling="no";
			container.append(iframe);
			
			iframe.contentWindow.document.open();
			iframe.contentWindow.document.write(html);//这里用iframe是因为某些字典的description中含有body样式，导致样式污染。
			iframe.contentWindow.document.close();
            iFrameResize({
                log:false,
                checkOrigin:false,
                resizeFrom:'child',
                heightCalculationMethod:'documentElementOffset',
                warningTimeout:0,
            },iframe);
			
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}



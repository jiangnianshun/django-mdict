//模板字符串
var script=`
<script src="/static/jquery-3.4.1/jquery-3.4.1.min.js"><\/script>
<script src='/static/mdict/iframe-resizer-master/js/iframeResizer.contentWindow.min.js'></script>
<script src="/static/mdict/js/transform.js"></script>
<script src="/static/mdict/js/base_func.js"></script>
<script src="/static/mdict/js/mdict_base.js"></script>
<script src="/static/mdict/js/iframe_base.js"></script>
<script src="/static/mdict/js/mdict.js"></script>
<script src="/static/mdict/js/init_iframe.js"></script>
`;

var search_history=new Array();

var style=`
<style>
html,body{
	padding:0;
}
img{
	max-width:100% !important;
}
/*这里如果设置全部元素强制max-width:100%，slangit.com中smh词条的svg会特别大。*/
.mdict-tooltip{
	background-color:gray;
	color:#EEEEEE;
	border-radius:5px;
	font-size:1.1em;
	z-index:999;
}
.mdict-tooltip span{
	white-space:nowrap;
	margin:5px;
}
.mdict-tooltip span a{
	background-color:gray;
	text-decoration:none;
	color:#EEEEEE;
	font-style:normal;
}
</style>
`
var style_font=`
<style>
@font-face {
font-family: FSung-m;
src: url(/media/font/全宋體/FSung-m.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-1;
src: url(/media/font/全宋體/FSung-1.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-2-1;
src: url(/media/font/全宋體/FSung-2-1.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-2-2;
src: url(/media/font/全宋體/FSung-2-2.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-3;
src: url(/media/font/全宋體/FSung-3.ttf);
font-display:swap;
}
@font-face {
font-family: FSung-F;
src: url(/media/font/全宋體/FSung-F.ttf);
font-display:swap;
}
*{font-family:Arial,FSung-p,FSung-m,FSung-1,FSung-2-1,FSung-2-2,FSung-3,FSung-F !important;}
</style>
`

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
		
		for(var i=0;i<d.length;i++){
			var record=d[i];

			var mdx_name=record["mdx_name"];
			var mdx_entry=record["mdx_entry"];
			var mdx_record=record["mdx_record"];
			var mdx_pk=record["pk"];
			
			if(need_clear){
				var s_id=i;
			}else{
				var s_id=iframe_length+i;
				
			}

			var s_parent='#card-container';
			if($('#config-card-show').prop('checked')){
                s_parent='';
			}

			var s=`
			<div class='card'>
				<div class='card-header'>
					<a class='card-link collapsed' href='#card-element-${s_id}' data-toggle='collapse' >
					<span class='badge badge-pill badge-info'>${html_escape(mdx_entry)}</span>${html_escape(mdx_name)}</a>
				</div>
				<div class='collapse' id='card-element-${s_id}' data-parent='${s_parent}'>
					<div class='card-body' id='card-body-${s_id}'>
					</div>
				</div>
			</div>
			`;
			/*
			由于mdx_entry可能包含<等字符导致显示出错，因此需要转义。
			data-toggle='collapse'操作是控制展开和折叠
			href='#card-element-"+i+"'操作目标是#card-element-"+i+"
			collapse默认折叠
			collapse show默认展开
			如果默认折叠，那么iframe的高度不正确，展开后只显示一条缝。因此先默认展开再循环折叠。
			
			data-parent='#card-container'
			在card-container的子元素的所有可折叠元素，同一时间只能有一个展开。
			*/
		   
            var force_font=$('#config-force-font',parent.document).prop("checked");
			if(force_font){
			    var html=style+style_font+script+"<body data-pk="+mdx_pk+">"+mdx_record+"</body>";
			}else{
			    var html=style+script+"<body data-pk="+mdx_pk+">"+mdx_record+"</body>";
			}

			//script加到最后，因为enwikipart1查gucci，最后有未完成的注释<!--，导致script被注释掉。

			var iframe = document.createElement('iframe');
			//iframe.width="100%";
			//iframe.height="auto";
			iframe.id="iframe-"+s_id;
			//iframe.setAttribute("data-pk",mdx_pk);
			//iframe.src = 'data:text/html;charset=utf-8,' + encodeURIComponent(html);
			//html中的#号会被截断，导致iframe读取不完整，因此要编码，而encodeURIComponent()会编码#号，但是encodeURI()不会编码，问题是使用encodeURIComponent()载入的子页面，css无法载入。
			
			var card_body_id="#card-body-"+s_id;
			var card_mdict_i=$(card_body_id);
			if(card_mdict_i.length>0){//清理同一时间的多次异步产生的多个重复词条
				card_mdict_i.children().remove();
			}else{
				container.append(s);
			}
			$(card_body_id).append(iframe);
			
			(function(iframe,html){//通过闭包来避免for循环事件绑定中的赋值问题
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
					    html=html.replace(/\\n/g,'<br />');
					    //懶虫簡明英漢漢英詞典错误的使用\n换行，很少词典有这个问题，因此放在前端处理

						iframe.contentWindow.document.open();
						iframe.contentWindow.document.write(html);
						iframe.contentWindow.document.close();

						$(iframe).contents().find('span[src]').each(function(){
						    //朗文现代5查jarring,jarringly,结果是span,span的src是base64图片，浏览器中不显示，这里重新生成img标签。
						    var new_img=$('<img>',{
                                src:$(this).attr('src')
                            })
						    $(this).after(new_img);
						});

						
						iFrameResize({
							log:false,
							checkOrigin:false,
							resizeFrom:'child',
							//inPageLinks:true,
							heightCalculationMethod:'lowestElement',
							//heightCalculationMethod:'max',
							//minHeight:60,
							warningTimeout:0,
//							onInit: function(iframe_a){
//							    console.log(iframe_a);
//							},
//							onResized: function(messageData) {
//									//if(card.find('.defaultscale').val()==''){
//									    //card.find('.defaultscale').trigger('click');
//									    //iframe加载完后，点击一下defaultscale来获取body正确的fontstyle
//									//}
//							},
						},iframe);
						$(iframe).attr('data-content-fill','true');
						
						/*
						log:false不显示debug信息
						checkOrigin:false不对iframe的url进行检查
						heightCalculationMethod设置为max会多次比较，导致在chrome上加载图片的iframe闪烁更严重。
						默认iframe也是不包含margin的，使用lowestElement才是最正确的高度，但这会引起效率问题。
						高度应该选默认，不能选max，选max会导致在手机上长iframe有明显卡顿
						有一个模式好像会导致内置词典获取的高度不正确？？
						resizeFrom:'child'设置当iframe变化时更新状态，默认是窗口变化时更新状态
						warningTimeout:0,抑制iframeresizer的警告信息
						第二个参数是iframe的dom对象，如果不设置，则对全部的iframe都生效。	
						*/
					}
				});
			
				card.on('shown.bs.collapse',function(){
					//shown.bs.collapse是collapse展开完成事件
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
				});

				card.find('.defaultscale').click(function(){
					var iframe_body=card.find('iframe').contents().find('body');
					if($(this).val()==''){
					    $(this).val(parseInt(iframe_body.css('font-size')));
					}
					iframe_body.animate({ fontSize: $(this).val() });
				});

			})(iframe,html);
		}
		return [current_page,total_page]
	}
	
}


function add_to_history(query,result_num){
    if(!(query in search_history)){//设置本页面查询历史，重复的查询不加入
        search_history[query]=result_num;
        var li_h=$('<li>',{
            text:"查询："+query+"    结果："+result_num,
        });
        li_h.appendTo('#search-history');
        li_h.click(function(){
            if(query!=$("#query").val()){
                $("#query").val(query);
                $("#mdictquery").trigger("click");
            }
            $("#modal-container-history").modal("hide");
        })

    }
}

function query_mdict(query,container,page,need_clear,is_over){
	var dic_group=$('#dic-group option:selected').attr('data-pk');
	var data={"query":query,"dic_group":dic_group,"page":page,"force_refresh":$('#config-force-refresh').prop('checked')};
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

				$("#result_num").text(result_num+"个结果");
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
                    <a class='card-link collapsed' href='#card-element-${s_id}' data-toggle='collapse' >
                    <span class='badge badge-pill badge-info'>${html_escape(mdx_entry)}</span>${html_escape(mdx_name)}</a>
                </div>
                <div class='collapse' id='card-element-${s_id}' data-parent='#card-container'>
                    <div class='card-body' id='card-body-${s_id}'>
                    </div>
                </div>
            </div>
            `;

            var iframe = document.createElement('iframe');
            iframe.src=item.attr("data-url").replace('%WORD%',query);
            iframe.id="iframe-"+s_id;
            iframe.height='600px';

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
                    show_first_card();

                    //var script = document.getElementById(iframe.id).contentWindow.document.createElement('script');
                    //script.src='/static/mdict/iframe-resizer-master/js/iframeResizer.contentWindow.min.js';
                    //跨域，无法获取iframe的document，也插入js
                }
            })(iframe)
        }else{
            var url=item.attr("data-url").replace('%WORD%',query);
            window.open(url,"_blank")
        }
    });

}

function process_time(time){
	if(time<1000){
		return time+'毫秒';
	}else{
		return time/1000+'秒';
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
            if(ob.children("audio").length==0){
                ob.append('<audio style="display:none;"></audio>');
            }
            ob.children("audio")[0].src=URL.createObjectURL(blob);

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
        if(ob.children("audio").length==0){
            ob.append('<audio style="display:none;"></audio>');
        }
        ob.children("audio")[0].src=URL.createObjectURL(blob);
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
					<button type="button" class="close" data-dismiss="alert"
							aria-hidden="true">
						&times;
					</button>
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

function set_mdict_enable(obj,pk){
    var data={"mdict_pk":pk,"mdict_enable":$(obj).prop("checked")};
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

function get_mdict_list(container){//载入词典列表
	$.ajax({
		url:"/mdict/mdictlist/",
		contentType:'json',
		type:'GET',
		success:function(data){
			var d=$.parseJSON(data);
			$("#dic_num").text(d.length);
			for(var i=0;i<d.length;i++){
				var dic_name=d[i]["dic_name"];
				var dic_icon=d[i]["dic_icon"];
				var dic_pror=d[i]["dic_pror"];
				var dic_pk=d[i]["dic_pk"];
				var dic_enable=d[i]["dic_enable"];

				var checked="";

				if(dic_enable){checked="checked";}

				var checkbox_html=`
                            <div class="custom-control custom-checkbox" style="display:inline;">
                                <input type="checkbox" class="custom-control-input" id="customControlInline${i}" ${checked} onchange="set_mdict_enable(this,${dic_pk})">
                                <label class="custom-control-label" for="customControlInline${i}" style="display:inline;vertical-align:middle;"></label>
                            </div>
                            `
				var s="<div class='card-header'>"+checkbox_html+"<img class='dic-icon' src="+space_escape(dic_icon)+"></img><span class='badge badge-pill badge-light'>"+dic_pror+"</span><a class='mdict-list-mark' href='/mdict/dic/?dic_pk="+dic_pk+"'>"+html_escape(dic_name)+"</a></div>";

				container.append(s);
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
			
			var h_line="<div style='width:100%; border:1px solid gray;margin-top:1em;margin-bottom:1em;'></div>";
			var title="";
			var description="";
			var num_entrys="共有词条"+thousands(num)+'条';
			var other_attributes="";
			for(var key in header){
				if(key!="StyleSheet"&&header[key].length>0){//不显示StyleSheet属性和空属性
					if(key=="Title"){
						title=`<div>${header[key]}</div>`;
					}else if(key=="Description"){
						description=`<div>${header[key]}</div>`;
					}else{
						other_attributes+=`<div>${key}：${header[key]}</div>`;
					}
					
				}
			}
			
			var style="<style>html,body{margin:0;padding:0;}img{max-width:100%;}</style>";
			
			var html=style+title+description+h_line+num_entrys+h_line+other_attributes+script;
			
			var iframe = document.createElement('iframe');
			iframe.width="100%";
			iframe.height="100%";
			iframe.id="dic-header";
			iframe.scrolling="no";
			container.append(iframe);
			
			iframe.contentWindow.document.open();
			iframe.contentWindow.document.write(html);//这里用iframe是因为某些字典的description中含有body样式，导致样式污染。
			iframe.contentWindow.document.close();
			resize_iframe_height()
			
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}



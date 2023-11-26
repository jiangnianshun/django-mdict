var script=`
<script src='/static/mdict/iframe-resizer/js/iframeResizer.contentWindow.min.js'></script>
`;

var is_dragging=false;

function set_body_height(){
    $("body").height($(window).height()-60);
}

function start_modal(obj){
    if(!is_dragging){
        var dic_pk=$(obj).attr('data-pk');
        $("#modal-shelf-dic").attr('data-pk',dic_pk);
        var dic_name=$(obj).attr('data-name');
        get_header($("#modal-shelf-dic .modal-body"),dic_pk,dic_name,1);
    }
}

function start_offcanvas(obj){
    if(!is_dragging){
        var dic_pk=$(obj).attr('data-pk');
        $("#offcanvas-shelf-dic").attr('data-pk',dic_pk);
        var dic_name=$(obj).attr('data-name');
        get_header($("#offcanvas-shelf-dic .offcanvas-body"),dic_pk,dic_name,2);
    }
}

function set_canvas(canvas_id) {
    var canvas = document.getElementById(canvas_id);
    canvas.clientWidth=110;
    canvas.clientHeight=150;
}

var canvas1 = document.getElementById('textCanvas1');
var tCtx1 = canvas1.getContext('2d');
var img_width = 110;
var img_height = 150;

function draw_canvas(){
    var clg = tCtx1.createLinearGradient(0,0,0,150);
    clg.addColorStop(0,'#1e1e1e'); // 第一个参数可以设定渐变位置 数字0~1之间
    clg.addColorStop(1,'#4f4f4f');
    tCtx1.fillStyle = clg;
    tCtx1.fillRect(0,0,img_width*devicePixelRatio,img_height*devicePixelRatio);
    tCtx1.fillStyle = '#1e1e1e';
    tCtx1.fillRect(5*devicePixelRatio,0,1*devicePixelRatio,img_height*devicePixelRatio);
    tCtx1.fillStyle = '#a90329';
    tCtx1.fillRect((img_width-15)*devicePixelRatio,0,6*devicePixelRatio,15*devicePixelRatio);
}

function init_canvas(){
    tCtx1.canvas.width = parseInt(getComputedStyle(canvas1, null)['width']) * devicePixelRatio;
    tCtx1.canvas.height = parseInt(getComputedStyle(canvas1, null)['height']) * devicePixelRatio;
    set_canvas('textCanvas1');
    draw_canvas();
}

function refresh_dic_prior(){
    $.ajax({
        url:'/mdict/getprior/',
        contentType:'json',
        type:'GET',
        success:function(data){
            let pk_list=$.parseJSON(data);
            for(let i=0;i<pk_list.length;i++){
                let tpk=pk_list[i][0];
                let tprior=pk_list[i][1];
                let col=$('.card[data-pk="'+tpk+'"]').parent();
                col.find('.card-body .text-primary').text(tprior);
            }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function edit_dic(cur_pk,prev_pk){
    let data={'cur_pk':cur_pk,'prev_pk':prev_pk}
    $.ajax({
        url:'/mdict/editdic/',
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
            if(data=='success'){
                refresh_dic_prior();
            }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function init_cols(){
    $(".row").sortable({
        revert:true,
        cursor:"move",
        opacity:0.75,
        helper:"clone",
        items:".sorting-initialize",
        forceHelperSize:true,
        forcePlaceholderSize:true,
        start:function(event,ui){
            is_dragging=true;
        },
        stop:function(event,ui){
            is_dragging=false;
            let cur_ele=ui.item[0];
            let prev_ele=cur_ele.previousElementSibling;
            let cur_pk=$(cur_ele).children('.dic-container').attr('data-pk');
            let prev_pk=$(prev_ele).children('.dic-container').attr('data-pk');
            edit_dic(cur_pk,prev_pk);
        }
    });
    $(".row").children(".col").one("mouseenter",function(){
        //分批加载，避免卡顿
        if(!$(this).hasClass("sorting-initialize")){
            let col_list=$(".row").children(".col");
            let cur_index=$(this).index();
            let s_index=0;
            let e_index=col_list.length-1;
            if(cur_index-70>0){s_index=cur_index;}
            if(s_index+140<col_list.length){e_index=s_index+140;}
            for(let i=s_index;i<=e_index;i++){
                $(col_list[i]).addClass("sorting-initialize");
            }
            $(".row").sortable('refresh');
        }
    });
}

function get_items(container,style){
    if(style==2){init_canvas();}
    $.ajax({
        url:"/mdict/getmdictlist/",
        contentType:'json',
        type:'GET',
        success:function(data){
            var d=$.parseJSON(data);
            var ts="";
            for(var i=0;i<d.length;i++){
                var dic_name=d[i]["dic_name"];
                var dic_file=d[i]["dic_file"];
                var dic_icon=d[i]["dic_icon"];
                var dic_pror=d[i]["dic_pror"];
                var dic_pk=d[i]["dic_pk"];
                var dic_enable=d[i]["dic_enable"];
                var dic_es_enable=d[i]["dic_es_enable"]
                var dic_type=d[i]["dic_type"];

                var dic_id='dic-'+i;
                if(style==1){
                    var s=`
                    <div class="col">
                        <div class="card shadow dic-container" title="${html_escape(dic_name,false)}" data-pk=${dic_pk} data-name="${html_escape(dic_name,false)}" data-file="${html_escape(dic_file,false)}" onclick="start_modal(this)">
                            <div class="card-body text-center">
                                <img src="${html_escape(dic_icon,false)}"></img>
                                <div class="card-title"><b class="text-primary">${dic_pror}</b>&nbsp;${html_escape(dic_name,false)}</div>
                            </div>
                        </div>
                    </div>
                    `
                }else{
                    if(dic_icon.indexOf("/static")==0){
                        var s=`
                        <div class="col">
                            <span class='book dic-container' title="${dic_pk}-${html_escape(dic_name,false)}" data-pk=${dic_pk} data-name="${html_escape(dic_name,false)}" data-file="${html_escape(dic_file,false)}" onclick="start_offcanvas(this)">
                                <img id=${dic_id} src=""></img>
                            </span>
                        </div>
                        `
                    }else{
                        var s=`
                        <div class="col">
                            <span class='book dic-container' title="${dic_pk}-${html_escape(dic_name,false)}" data-pk=${dic_pk} data-name="${html_escape(dic_name,false)}" data-file="${html_escape(dic_file,false)}" onclick="start_offcanvas(this)">
                                <img src="${html_escape(dic_icon,false)}"></img>
                            </span>
                        </div>
                        `
                    }
                }
                ts+=s;
            }
            container.append(ts);
            set_dic_num();
            if(style==2){
                setTimeout(function(){//异步运行
                    for(var i=0;i<d.length;i++){
                        var dic_name=d[i]["dic_name"];
                        var dic_icon=d[i]["dic_icon"];
                        var dic_id='dic-'+i;

                        //绘制封面图
                        if(dic_icon.indexOf("/static")==0){
                            (function(dic_name,dic_id){
                                var canvas2 = document.getElementById('textCanvas2');
                                var tCtx2 = canvas2.getContext('2d');
                                tCtx2.canvas.width = parseInt(getComputedStyle(canvas2, null)['width']) * devicePixelRatio;
                                tCtx2.canvas.height = parseInt(getComputedStyle(canvas2, null)['height']) * devicePixelRatio;
                                set_canvas('textCanvas2');
                                tCtx2.drawImage(document.getElementById('textCanvas1'),0,0);
                                tCtx2.fillStyle = '#ffffff';
                                tCtx2.font = 12*devicePixelRatio+'px Arial';

                                var new_text_array = new Array();
                                var row_width = 0;
                                var row_text = "";
                                var row_max_width = (img_width-7-15)*devicePixelRatio;

                                for(var ti=0;ti<dic_name.length;ti++){
                                    row_width+=tCtx2.measureText(dic_name[ti]).width;
                                    row_text+=dic_name[ti];
                                    if(row_width>=row_max_width){
                                        new_text_array.push(row_text);
                                        row_width=0;
                                        row_text="";
                                    }else if(ti==dic_name.length-1){
                                        new_text_array.push(row_text);
                                    }
                                }

                                var text_height=55*devicePixelRatio;
                                if(new_text_array.length>1){
                                    var text_height=(parseInt((150-15)/new_text_array.length))*devicePixelRatio;
                                    if(text_height>55){text_height=55;}
                                }

                                for(var ti=0;ti<new_text_array.length;ti++){
                                    tCtx2.fillText(new_text_array[ti], 8*devicePixelRatio, (ti+1)*text_height, img_width*devicePixelRatio);
                                }

                                var imageElem = document.getElementById(dic_id);
                                imageElem.src = tCtx2.canvas.toDataURL();
                            })(dic_name,dic_id);
                        }
                    }
                },0);
            }
            if(is_PC()){init_cols();}
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function get_header(container, dic_pk, dic_name, type){
    container.empty();

    if(type==1){
        $('#modal-shelf-dic-title').text(dic_name);
    }else{
        $('#offcanvas-shelf-dic-title').text(dic_name);
    }

    var data={"dic_pk":dic_pk,"is_dic":false};
    $.ajax({
        url:"/mdict/getdicinfo/",
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
            //var num_entrys="词条数量："+thousands(num);
            var num_entrys=thousands(num);
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

//            description=description.replace('height="100%"','').replace("heigth='100%'",'');

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
            iframe.height="95%";
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

            if(type==1){
                var modal_shelf_dic = new bootstrap.Modal(document.getElementById('modal-shelf-dic'), {});
                modal_shelf_dic.show();
            }else{
                var offcanvas_shelf_dic = new bootstrap.Offcanvas(document.getElementById('offcanvas-shelf-dic'), {});
                offcanvas_shelf_dic.show();
            }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function shelf_dic_btn(type1,type2){
    if(type1==1){
        var dic_pk=$("#modal-shelf-dic").attr('data-pk');
    }else{
        var dic_pk=$("#offcanvas-shelf-dic").attr('data-pk');
    }
    if(type2==0){
        window.open('/mdict/dic/'+dic_pk+'/');
    }else if(type2==1){
        window.open('/mdict/esdic/'+dic_pk+'/');
    }else if(type2==2){
        window.open('/admin/mdict/mdictdic/'+dic_pk+'/');
    }
}

function open_path(type1){
    if(type1==1){
        var dic_pk=$("#modal-shelf-dic").attr('data-pk');
    }else{
        var dic_pk=$("#offcanvas-shelf-dic").attr('data-pk');
    }
    $.ajax({
        url:"/mdict/openpath/",
        contentType:'json',
        type:'GET',
        data:{"dic_pk":dic_pk},
        success:function(data){
            console.log(data);
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function set_dic_num(){
    $("#dic-num").text($(".col:visible").length);
}

function start_dic_filter(group_pk){
    data={"dic_group":group_pk};
    $.ajax({
        url:"/mdict/getpkingroup/",
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
        var pk_list=$.parseJSON(data);
        var col_list=$(".col");
        if(pk_list.length==0&&group_pk<=0){
            $(col_list).each(function(){$(this).show();});
            set_dic_num()
        }else{
            for(var i=0;i<col_list.length;i++){
                var dic_pk=parseInt($(col_list[i]).children('.dic-container').attr('data-pk'));
                var pk_pos=$.inArray(dic_pk,pk_list);
                if(pk_pos<0){
                    $(col_list[i]).hide();
                }else{
                    $(col_list[i]).show();
                }
            }
            set_dic_num();
        }

        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function init_dropdown(){
    $.ajax({
        url:"/mdict/getdicgroup/",
        contentType:'json',
        type:'GET',
        success:function(data){
        var dic_group=$.parseJSON(data);
        for(var i=0;i<dic_group.length;i++){
            var ele='<li onclick="start_dic_filter('+dic_group[i][0]+')"><span class="dropdown-item" data-pk='+dic_group[i][0]+'>'+dic_group[i][1]+'</span></li>'
            $('#dic-group').append($(ele));
        }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function init_mdict_filter(){
    $("#mdict-filter-input").bind("input propertychange",function(event){
        //juery的change事件，只有当input没有聚焦的时候才能触发，input propertychange能检测input输入过程中的变化
        var txt=$.trim($(this).val().toLowerCase( ));
        var item_list=$(".col");
        if(txt.length>0){//延时有问题
            last=event.timeStamp;
            //利用event的timeStamp来标记时间，这样每次事件都会修改last的值，注意last必需为全局变量
            setTimeout(function(){
            //设时延迟0.5s执行
                if(last-event.timeStamp==0){
                //如果时间差为0（也就是你停止输入0.5s之内都没有其它的keyup事件发生）则做你想要做的事
                    for(var i=0;i<=item_list.length;i++){
                        var item_a=$(item_list[i]).find('.dic-container');
                        if(item_a.length>0){
                            var title=item_a.attr('data-name').toLowerCase();
                            if(title=="")continue;
                            var file=item_a.attr('data-file').toLowerCase();

                            if(t2s(title).indexOf(txt)==-1&&s2t(title).indexOf(txt)==-1&&t2s(file).indexOf(txt)==-1&&s2t(file).indexOf(txt)==-1){
                                $(item_list[i]).hide();
                            }else{
                                $(item_list[i]).show();
                            }
                        }
                    }
                }
                set_dic_num();
            },500);
        }else{
           last=event.timeStamp;
           setTimeout(function(){//这里也要定时，否则在手机上，这里运行快，上面延时，快速删除时，显示结果不对
               for(var i=0;i<=item_list.length;i++){
                    $(item_list[i]).show();
               }
               set_dic_num();
           },500);
        }
    })
}
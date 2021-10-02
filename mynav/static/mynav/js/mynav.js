function init_mynav_filter(){
    $("#mynav-filter-input").bind("input propertychange",function(event){
        //juery的change事件，只有当input没有聚焦的时候才能触发，input propertychange能检测input输入过程中的变化
        var txt=$.trim($(this).val().toLowerCase());
        var item_list=$(".col");
        var card_list=$(".my-card-group");
        if(txt.length>0){//延时有问题
            last=event.timeStamp;
            //利用event的timeStamp来标记时间，这样每次事件都会修改last的值，注意last必需为全局变量
            setTimeout(function(){
            //设时延迟0.5s执行
                if(last-event.timeStamp==0){
                //如果时间差为0（也就是你停止输入0.5s之内都没有其它的keyup事件发生）则做你想要做的事
                    for(var i=0;i<=item_list.length;i++){
                        var item_a=$(item_list[i]).find('.web-site');
                        var item_href=$(item_list[i]).attr('href');
                        if(typeof(item_href)=='undefined'){
                            item_href='';
                        }
                        if(item_a.length>0){
                            var title=item_a.text().toLowerCase();
                            if(title=="")continue;
                            if(t2s(title).indexOf(txt)==-1&&s2t(title).indexOf(txt)==-1&&item_href.indexOf(txt)==-1){
                                $(item_list[i]).hide();
                            }else{
                                $(item_list[i]).parents(".my-card-group").show();
                                $(item_list[i]).show();
                            }
                        }
                    }
                }
                for(var i=0;i<=card_list.length;i++){//隐藏为空的组
                    var visible_col=$(card_list[i]).find(".col:visible");
                    if(visible_col.length==0){
                        $(card_list[i]).hide();
                    }else{
                        $(card_list[i]).show();
                    }
                }
            },500);
        }else{
           last=event.timeStamp;
           setTimeout(function(){//这里也要定时，否则在手机上，这里运行快，上面延时，快速删除时，显示结果不对
               for(var i=0;i<=item_list.length;i++){
                    $(item_list[i]).parents(".my-card-group").show();
                    $(item_list[i]).show();
               }
           },500);
        }
    })
}

$('.go-top').click(function(){//返回顶部
    $('html,body').animate({scrollTop:0},'slow');
});

function fill_dropdown(item){
    let span_ele=$(item).children('span');
    $("#group-list").text(span_ele.text());
    $("#group-list").attr("data-pk",span_ele.attr("data-pk"));
}

function init_dropdown(){
    $.ajax({
        url:'/mynav/getgroup/',
        contentType:'json',
        type:'GET',
        success:function(data){
            let group_list=$.parseJSON(data);
            let site_group=$('#site-group');
            site_group.empty();
            for(let i=0;i<group_list.length;i++){
                var ele='<li onclick="fill_dropdown(this)"><span class="dropdown-item" data-pk='+group_list[i][0]+'>'+group_list[i][1]+'</span></li>';
                site_group.append($(ele));
            }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
            //alert(jqXHR.status);
            //alert(jqXHR.readyState);
            //alert(jqXHR.statusText);
            //alert(textStatus);
            //alert(errorThrown);
        },
    })
}

function init_tooltip(){
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
}

function init_contents(){
    $.ajax({
        url:'/mynav/getsite/',
        contentType:'json',
        type:'GET',
        success:function(data){
            let group_list=$.parseJSON(data);
            let ele_str='';
            for(let i=0;i<group_list.length;i++){
                let group_item=group_list[i];
                let group_name=group_item[0];
                let sites_list=group_item[1];

                ele_str+=`
                <div class="card my-card-group" id='card-${i}'>
                    <div class="card-header">
                        <span class='text-secondary card-link' href='#card-element-${i}' data-bs-toggle='collapse' aria-controls="#card-element-${i}">${group_name}</span>
                    </div>
                    <div class="row card-body collapse show" id='card-element-${i}'>
                `
                for(let j=0;j<sites_list.length;j++){
                    let site=sites_list[j];
                    let site_id=site[0];
                    let site_name=site[1];
                    let site_url=site[2];
                    let site_icon=site[3];
                    let site_brief=site[4];
                    if(site_icon){
                        ele_str+=`
                            <div class="col">
                                <div class="card shadow" tabindex="0" data-bs-toggle="tooltip" title="${site_brief}">
                                    <div class="card-body text-center">
                                        <a class="web-site" href="${site_url}" target="_blank"><img src="/media/icon/${site_id}.ico" style="margin-right:3px;"></img>${site_name}</a>
                                    </div>
                                </div>
                            </div>
                        `
                    }else{
                        ele_str+=`
                            <div class="col">
                                <div class="card shadow" tabindex="0" data-bs-toggle="tooltip" title="${site_brief}">
                                    <div class="card-body text-center">
                                        <a class="web-site" href="${site_url}" target="_blank">${site_name}</a>
                                    </div>
                                </div>
                            </div>
                        `
                    }
                }
                ele_str+=`
                    </div>
                </div>
                `
            }
            $('#main-contents').empty();
            $('#main-contents').append(ele_str);

            $('.my-card-group a').click(function(e){
                e.preventDefault();
                let url=$(this).attr("href");
                let new_url=url;
                if(url.indexOf('://')==-1){
                    if(url[0]=='/'){
                        new_url='http:/'+url;
                    }else{
                        new_url='http://'+url;
                    }
                }
                window.open(new_url);
            })

            init_tooltip();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
            //alert(jqXHR.status);
            //alert(jqXHR.readyState);
            //alert(jqXHR.statusText);
            //alert(textStatus);
            //alert(errorThrown);
        },
    })
}

//添加网站
function addsite(){
    var site_name=$('#site-name').val();
    var site_url=$('#site-url').val();
    var site_group=$("#group-list").attr("data-pk");
    var site_priority=$('#site-priority').val();
    var site_brief=$('#site-brief').val();

    if(!site_name||!site_url){
        alert("网站名称和地址不能为空！");
        return;
    }
    if(!site_priority){site_priority=1;}

    var data={'site_name':site_name,'site_url':site_url,'site_group':site_group,'site_priority':site_priority,'site_brief':site_brief};
    $.ajax({
        url:'/mynav/addsite/',
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
            console.log('内容存储成功！'+data);
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
            //alert(jqXHR.status);
            //alert(jqXHR.readyState);
            //alert(jqXHR.statusText);
            //alert(textStatus);
            //alert(errorThrown);
        },
    }).done(function(){
            //window.location.reload();
            init_contents();
    });
}

function addgroup(){
    var group_name=$('#group-name').val();
    var group_priority=$('#group-priority').val();
    if(!group_name){alert('分组名不能为空！');return;}
    if(!group_priority){group_priority='1';}
    var data={'group_name':group_name,'group_priority':group_priority}
    $.ajax({
        url:'/mynav/addgroup/',
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
            console.log('分组创建成功！'+data);
            init_dropdown();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
            //alert(jqXHR.status);
            //alert(jqXHR.readyState);
            //alert(jqXHR.statusText);
            //alert(textStatus);
            //alert(errorThrown);
        },
    })
}

function init_event(){
    $('#expand-all').click(function(){
        $('.my-card-group').each(function(){
            let show_cards=$(this).find('.collapse.show');
            if(show_cards.length==0){$(this).find('.card-header span').trigger('click');}
        })
    })
    $('#collapse-all').click(function(){
        $('.my-card-group').each(function(){
            let show_cards=$(this).find('.collapse.show');
            if(show_cards.length>0){$(this).find('.card-header span').trigger('click');}
        })
    })
}

function init_mynav(){
    init_mynav_filter();
    init_contents();
    init_event();
}
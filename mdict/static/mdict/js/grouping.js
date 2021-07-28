function get_data_path(node_id){
    let data_path="";
    if(node_id!="#"){
        let cur_ele=$("#"+node_id);
        let pre_ele=$("#"+node_id).parent();
        if(pre_ele.is("ul")){
            pre_ele=pre_ele.parent();
        }
        let cur_path=cur_ele.attr("data-path");
        let pre_path=pre_ele.attr("data-path");
        while(typeof(pre_path)!="undefined"){
            if(pre_path!="_root"){
                cur_path=pre_path+"/"+cur_path;
            }
            cur_ele=pre_ele;
            pre_ele=cur_ele.parent();
            if(pre_ele.is("ul")){
                pre_ele=pre_ele.parent();
            }
            pre_path=pre_ele.attr("data-path");
        }
        data_path=cur_path;
    }
    return data_path
}

function init_jstree(){
    $("#grouping-left").jstree({
        "plugins" : ["checkbox","search"],
        "core" : {
            "data" : {
                "url" : "mdictpath/",
                "data" : function (node) {
                    return { "path" : get_data_path(node.id) };
                }
            }
        }
    }).bind("search.jstree", function (e, data) {
        let snodes=data.res;
        for(let ri=0;ri<snodes.length;ri++){
            if(!$("#"+snodes[ri]).hasClass("jstree-open")&&!$("#"+snodes[ri]).hasClass("jstree-closed")){
                //只选择文件，不选择文件夹。
                $("#grouping-left").jstree(true).select_node(snodes[ri]);
            }
        }
    });
    $("#grouping-right").jstree({
        "plugins" : ["contextmenu","dnd"],
        "contextmenu": {
            "items": function ($node) {
                let tree = $("#grouping-right").jstree(true);
                let cur_node=$("#"+$node.id);
                let dic_pk=cur_node.attr("data-pk");
                let prev_node=cur_node.parent().parent();
                let menu = {};
                if(cur_node.hasClass("dic-item")){
                    menu["Open"]={
                        "separator_before": false,
                        "separator_after": false,
                        "label": "打开",
                        "action": function (obj) {
                            if(cur_node.hasClass("dic-item")){
                                let url="/mdict/dic/"+dic_pk;
                                window.open(url);
                            }
                        }
                    };
                }
                menu["Edit"]={
                    "separator_before": false,
                    "separator_after": false,
                    "label": "编辑",
                    "action": function (obj) {
                        if(cur_node.hasClass("dic-item")){
                            let url="/admin/mdict/mdictdic/"+dic_pk;
                            window.open(url);
                        }else{
                            let url="/admin/mdict/mdictdicgroup/"+dic_pk;
                            window.open(url);
                        }
                    }
                };
                menu["Rename"]={
                    "separator_before": false,
                    "separator_after": false,
                    "label": "重命名",
                    "action": function (obj) {
                       tree.edit($node);
                    }
                };
                menu["Delete"]={
                    "separator_before": false,
                    "separator_after": false,
                    "label": "删除",
                    "action": function (obj) {
                        if(cur_node.hasClass("jstree-leaf")){
                            delete_item(cur_node.attr("data-pk"),prev_node.attr("data-pk"),false);
                        }else{
                            delete_item(cur_node.attr("data-pk"),prev_node.attr("data-pk"),true);
                        }
                        tree.delete_node($node);
                    }
                };
                return menu
            },
        },
        "dnd" : {
            "check_while_dragging" : true,
        },
        "core" : {
            "check_callback" : function(operation, node, node_parent, node_position, more){
                if (operation === "move_node") {
                    let cur_ele=$("#"+node.id);
                    if(cur_ele.hasClass("group-item")){
                        //节点是分组时禁止移动
                        return false;
                    }else if(node_position == 0){
                        //node_position,0插入，>0非插入的其他位置
                        //more,a之后,b之前,i插入
                        let par_ele=$("#"+node_parent.id);//新的父节点
                        if(par_ele.hasClass("dic-item")){
                            //节点是词典时禁止插入子元素
                            return false;
                        }
                    }
                }
                return true;
            },
            "data" : {
                "url" : 'mdictgroup/',
                "data" : function (node) {
                    let group_pk=0;
                    if(node.id!="#"){
                        let cur_ele=$("#"+node.id);
                        group_pk=cur_ele.attr("data-pk");
                    }
                    return { "group" : group_pk };
                }
            }
        },
    }).bind("rename_node.jstree", function (e, data) {
        let cur_node=$("#"+data.node.id);
        let text=data.text;
        let mark=text.indexOf("<span style=\"color:red;\">");
        if(mark>-1){
            text=text.substring(0,mark);
        }else{
            mark=text.indexOf("</span>");
            if(mark>-1){
                text=text.substring(0,mark);
            }
        }
        if(cur_node.hasClass("jstree-leaf")){
            rename_item(text,cur_node.attr("data-pk"),false);
        }else{
            rename_item(text,cur_node.attr("data-pk"),true);
        }
    }).bind("move_node.jstree", function (e, data) {
        //let node_ele = $('#' + data.node.id);
        //使用node_ele.attr("data-pk")取值有时候是undefined
        let par_ele = $('#' + data.parent);
        let old_par_ele = $('#' + data.old_parent);
        move_item(parseInt(data.node.li_attr["data-pk"]),par_ele.attr("data-pk"),old_par_ele.attr("data-pk"));
    });
}

function move_item(item_pk,new_group_pk,old_group_pk){
    data={"item_pk":item_pk,"new_group_pk":new_group_pk,"old_group_pk":old_group_pk};
    $.ajax({
        url:"/mdict/moveitem/",
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
            console.log(data);
            refresh_right_jstree();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function delete_item(item_pk,parent_pk,is_group){
    data={"item_pk":item_pk,"parent_pk":parent_pk,"is_group":is_group};
    $.ajax({
        url:"/mdict/deleteitem/",
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
            console.log(data);
            refresh_right_jstree();
            init_dropdown();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function rename_item(text,item_pk,is_group){
    data={"text":text,"item_pk":item_pk,"is_group":is_group};
    $.ajax({
        url:"/mdict/renameitem/",
        contentType:'json',
        type:'GET',
        data:data,
        success:function(data){
            console.log(data);
            refresh_right_jstree();
            init_dropdown();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function init_event(){
    $("#home").click(function(){
        window.location.href="/";
    });
    $("#create-group").click(function(){
        let group_name=$("#group-name").val();
        if(group_name!=""){
            let data={"group_name":group_name};
            $.ajax({
                url:"creategroup/",
                contentType:'json',
                type:'GET',
                data:data,
                success:function(data){
                    refresh_right_jstree();
                    init_dropdown();
                },
                error:function(jqXHR,textStatus,errorThrown){
                    alert(jqXHR.responseText);
                },
            });
        }
    });
    $("#expand-all").click(function(){
        $("#grouping-left").jstree("open_all");
    })
    $("#add-to-group").click(function(){
        let group_pk=$("#group-list").attr("data-pk");
        if(group_pk>0){
            let checked_path = [];
            let checked_eles=$("#grouping-left").jstree(true).get_checked();
            $.each(checked_eles,function () {
                if(!$("#grouping-left").jstree(true).is_disabled(this)){
                    let cur_node=$("#"+this);
                    let prev_node=cur_node.parent().parent();
                    if(prev_node.length>0){
                        if(prev_node.attr("id")=="grouping-left"||!$("#grouping-left").jstree(true).is_checked(prev_node.attr("id"))){
                            if(cur_node.hasClass('path-dir')){
                                checked_path.push(get_data_path(this));
                            }else{
                                checked_path.push(cur_node.attr("data-path"));
                            }
                        }
                    }
                }
            });
            if(checked_path.length>0){
                add_to_group(group_pk,checked_path)
            }
        }
    })
    var to = false;
    $('#grouping-filter').keyup(function () {
        if(to) { clearTimeout(to); }
        to = setTimeout(function () {
        var v = $('#grouping-filter').val();
        $('#grouping-left').jstree(true).deselect_all();
        $('#grouping-left').jstree(true).search(v);
        }, 250);
    });
}

function add_to_group(group_pk,checked_path){
    data={"group_pk":group_pk,"path":checked_path}
    $.ajax({
        url:"/mdict/addtogroup/",
        contentType:'json',
        type:'GET',
        data:data,
        traditional: true,
        success:function(data){
            console.log(data);
            refresh_right_jstree();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function refresh_right_jstree(){
    $('#grouping-right').jstree(true).refresh();
}

function fill_dropdown(item){
    let span_ele=$(item).children('span');
    $("#group-list").text(span_ele.text());
    $("#group-list").attr("data-pk",span_ele.attr("data-pk"));
}

function init_dropdown(){
    $("#group-list").text("分组");
    $("#group-list").attr("data-pk",0);
    $.ajax({
        url:"/mdict/dicgroup/",
        contentType:'json',
        type:'GET',
        success:function(data){
        var dic_group=$.parseJSON(data);
        $('#dic-group').empty();
        for(var i=0;i<dic_group.length;i++){
            var ele='<li onclick="fill_dropdown(this)"><span class="dropdown-item" data-pk='+dic_group[i][0]+'>'+dic_group[i][1]+'</span></li>'
            $('#dic-group').append($(ele));
        }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    });
}

function init_grouping(){
    init_jstree();
    init_event();
    init_dropdown();
}
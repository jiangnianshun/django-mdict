var iframe_script=`
<script src="/static/jquery/jquery.min.js"></script>
<script>
function ihyperlink(e){
    var ob=$(this);
    query=ob.attr("href")||null;
    e.preventDefault();
    if(query!=null){
        if(query.indexOf("entry")==0){//处理entry超链接
            var entry=query.substring(8);
            if(entry[0]!="#"){
                //entry#锚点
                //跳转到entry词条的锚点位置
                var sharp=entry.indexOf("#");
                if(sharp!=-1){
                    entry=entry.substring(0,sharp);
                }
                //自动查询超链接的entry
                var backslash=entry.indexOf("/");
                if(backslash==entry.length-1){
                    entry=entry.substring(0,backslash);
                }
                parent.get_entry(entry);
            }
        }else if(query.indexOf("http")==0||query.indexOf("www.")==0){
            window.open(query);
        }
    }
}
$(document).ready(function(){
    $("body").on("click", "a", ihyperlink);
});
</script>
`

var nodes=null;
var edges=null;
var nodeFilterValue="";
var nodeFilterValue2="";
var labelFilterValue="";
var nodesView=null;
var edgesView=null;
var network=null;

function check_node_filter(label,extra){
    let mark1=false;
    let mark2=false;
    if(nodeFilterValue==""&&nodeFilterValue2==""){
        mark1=true;
    }else if(nodeFilterValue!=""&&label.toLowerCase( ).indexOf(nodeFilterValue.toLowerCase( ))>-1) {
        mark1=true;
    }else if(nodeFilterValue2!=""&&label.toLowerCase( ).indexOf(nodeFilterValue2.toLowerCase( ))>-1){
        mark1=true;
    }
    if(labelFilterValue==""){
        mark2=true;
    }else if(extra.indexOf(labelFilterValue)>-1){
        mark2=true;
    }
    if(mark1&&mark2){return true;}
}

function create_filter(){
    const nodesFilter = (node) => {
        if(check_node_filter(node.label,node.extra)) {
            return true;
        }else{
            con_nodes=network.getConnectedNodes([node.id]);
            let mark=false;
            con_nodes.forEach(function(node_id){
                let con_node=nodes.get(node_id);
                if(check_node_filter(con_node.label,node.extra)) {
                    mark=true;
                }
            });
            if(mark){return true;}
        }
    };
    nodesView = new vis.DataView(nodes, {filter:nodesFilter});
}

function create_network(){
    var only_edge_node=$('#only-edge-node').prop("checked");
    var show_label=$('#show-label').prop("checked");
    var data={"only_edge_node":only_edge_node,"show_label":show_label};
    $.ajax({
        url:'/mdict/getnodes/',
        contentType:'json',
        data:data,
        type:'GET',
        success:function(data){
            var pdata=$.parseJSON(data);
            var node_list=pdata['nodes'];
            var edge_list=pdata['edges'];

            if(node_list.length==0){node_list=[{"id":0,"label":"目前没有内置词条！"}];}
            nodes = new vis.DataSet(node_list);
            edges = new vis.DataSet(edge_list);
            create_filter();
            var ndata={'nodes':nodesView,'edges':edges};
            network=set_data(ndata);
            init_network();
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function create_entry(entry,html,tpk){
    var entry_iframe=$("#entry-iframe");
    if(entry_iframe.length==0){
        var iframe = document.createElement('iframe');
        iframe.id="entry-iframe";
        iframe.width="100%";
        iframe.sandbox="allow-same-origin allow-scripts allow-popups allow-downloads";
        $('#builtin-container-entry .modal-body').append(iframe);
    }else{
        var iframe=entry_iframe[0];
    }
    iframe.setAttribute('data-pk',parseInt(tpk));
    iframe.contentWindow.document.open();
    iframe.contentWindow.document.write(html);
    iframe.contentWindow.document.close();
    iFrameResize({
        log:false,
        checkOrigin:false,
        resizeFrom:'child',
        heightCalculationMethod:'lowestElement',
        minHeight:'320px',
        warningTimeout:0,
        scrolling:true,
    },iframe);
    $("#builtin-container-title").text(entry);
    if(!$('#builtin-container-entry').hasClass('show')){
        var modal_entry = new bootstrap.Modal(document.getElementById('builtin-container-entry'), {});
        modal_entry.show();
    }
}

function get_entry(entry){
    $.ajax({
        url:'/mdict/getmymdictentry/',
        contentType:'json',
        type:'GET',
        data:{"entry":entry},
        success:function(data){
            var jdata=$.parseJSON(data);
            var tentry=jdata["entry"];
            var tcontent=jdata["content"];
            var tpk=jdata["pk"];
            var html='<style>html,body{height:320px;}</style><script src=\"/static/mdict/iframe-resizer/js/iframeResizer.contentWindow.min.js\"></script>'+tcontent+iframe_script;
            //设置iframe的html和body高度，否则前一次的高度会影响后一次。
            create_entry(tentry,html,tpk);
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function init_network(){
    network.on("click",function(params){
        var ids = params.nodes;
        var clickedNodes = nodes.get(ids);
        if(clickedNodes.length>0){
            var label=clickedNodes[0]["label"];
            get_entry(label);
        }
    })
}

function edit_node_btn(){
    var node_pk=$("#entry-iframe").attr('data-pk');
    if(typeof(node_pk)!='undefined'&&node_pk!='NaN'&&node_pk>0){
        window.open('/admin/mdict/mymdictentry/'+node_pk+'/');
    }else{
        window.open('/admin/mdict/mymdictentry/add/');
    }
}

function add_node(nodeData,callback){
    $('#mytooltip').val('');
    $('#mytooltip').show();
    $('#create-myentry').unbind('click');
    $('#create-myentry').click(function(){
        let node_label=$('#myentry-name').val();
        $('#mytooltip').hide();
        if(node_label!=''){
            $.ajax({
                url:'/mdict/addnode/',
                contentType:'json',
                type:'GET',
                data:{"label":node_label},
                success:function(data){
                    if(data=='success'){
                        nodeData.label=node_label;
                        nodeData.group='newGroup';
                        callback(nodeData);
                    }else{
                        callback(null);
                        $("#live-toast-body").text("error:"+data);
                        new bootstrap.Toast($("#live-toast")[0]).show();
                    }
                },
                error:function(jqXHR,textStatus,errorThrown){
                    callback(null);
                    alert(jqXHR.responseText);
                },
            })
        }
    })
}

function add_edge(edgeData,callback){
    if (edgeData.from != edgeData.to) {
        let edge_id=edgeData.from+'_'+edgeData.to;
        let edge=edges.get(edge_id);
        if(edge==null){
            edgeData.id=edge_id;
            let node_from=nodes.get(edgeData.from);
            let node_to=nodes.get(edgeData.to);
            $.ajax({
                url:'/mdict/addedge/',
                contentType:'json',
                type:'GET',
                data:{"from":node_from.label,"to":node_to.label},
                success:function(data){
                    if(data=='success'){
                        callback(edgeData);
                    }else{
                        callback(null);
                        $("#live-toast-body").text("error:"+data);
                        new bootstrap.Toast($("#live-toast")[0]).show();
                    }
                },
                error:function(jqXHR,textStatus,errorThrown){
                    callback(null);
                    alert(jqXHR.responseText);
                },
            })
        }else{
            callback(null);
            $("#live-toast-body").text("不能创建重复的箭头！");
            new bootstrap.Toast($("#live-toast")[0]).show();
        }
    }else{
        callback(null);
        $("#live-toast-body").text("不能创建指向自身的箭头！");
        new bootstrap.Toast($("#live-toast")[0]).show();
    }
}

function edit_edge(edgeData,callback){
    if (edgeData.from != edgeData.to) {
        let edge_id=edgeData.from+'_'+edgeData.to;
        let old_edge_id=edgeData.id;
        let old_node_from=nodes.get(parseInt(old_edge_id.split('_')[0]));
        let old_node_to=nodes.get(parseInt(old_edge_id.split('_')[1]));
        let node_from=nodes.get(edgeData.from);
        let node_to=nodes.get(edgeData.to);
        $.ajax({
            url:'/mdict/editedge/',
            contentType:'json',
            type:'GET',
            data:{"from":node_from.label,"to":node_to.label,"old_from":old_node_from.label,"old_to":old_node_to.label},
            success:function(data){
                if(data=='success'){
                    edgeData.id=edge_id;
                    callback(edgeData);
                    let old_node=edges.get(old_edge_id);
                    edges.remove(old_node);
                }else{
                    callback(null);
                    $("#live-toast-body").text("error:"+data);
                    new bootstrap.Toast($("#live-toast")[0]).show();
                }
            },
            error:function(jqXHR,textStatus,errorThrown){
                callback(null);
                alert(jqXHR.responseText);
            },
        })
    }else{
        callback(null);
        $("#live-toast-body").text("不能创建指向自身的箭头！");
        new bootstrap.Toast($("#live-toast")[0]).show();
    }
}

function edit_node(nodeData,callback){
    let node_label=nodeData.label;
    $.ajax({
        url:'/mdict/getnodeid/',
        contentType:'json',
        type:'GET',
        data:{"label":node_label},
        success:function(data){
            let jdata=$.parseJSON(data);
            if(jdata['pk']>0){
                let node_pk=jdata['pk'];
                window.open('/admin/mdict/mymdictentry/'+node_pk+'/');
                callback(nodeData);
            }else{
                $("#live-toast-body").text("error:"+jdata['error']);
                new bootstrap.Toast($("#live-toast")[0]).show();
            }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function set_data(data){
    var container = document.getElementById("mynetwork");
    if(data['nodes'].length<=400){
        var improved_layout=true;
    }else{
        var improved_layout=false;
        //false会更快地稳定，但是动画效果没有true好看。
    }
    var options = {
        physics: {
            stabilization: false,
            barnesHut: {
                    springLength: 200,
                },
        },
        edges:{
            arrows: {
                to: {
                    enabled: true,
                    type: "arrow"
                }
            },
            color: {
                color:'#848484',
                highlight:'#848484',
                hover: '#848484',
                inherit: 'from',
                opacity:1.0
            },
        },
        manipulation: {
            enabled: true,
            initiallyActive: true,
            addNode: add_node,
            addEdge: add_edge,
            //editNode: edit_node,
            editEdge: edit_edge,
            deleteNode: false,
            deleteEdge: false,
        },
        layout: {
            improvedLayout:improved_layout,
        },
        groups: {
            commonGroup:{},
            newGroup:{color:{background:'limegreen',highlight:{background:'yellowgreen'}}},
            noneGroup:{color:{background:'red',highlight:{background:'pink'}}},
        }
    };
    return new vis.Network(container, data, options);
}

function get_txt_value(val1,val2){
    let txt1=$.trim(val1.toLowerCase( ));
    let txt2=$.trim(val2.toLowerCase( ));
    if(typeof(txt1)=="undefined"){txt1="";}
    if(typeof(txt2)=="undefined"){txt2="";}
    return [txt1,txt2]
}

function refresh_filter(txt){
    if(nodesView!=null){
        nodeFilterValue=txt[0];
        nodeFilterValue2=txt[1];
        nodesView.refresh();
    }
}

function init_event(){
    $("#home").click(function(){
        window.location.href="/";
    });
    $('#filter-entry').click(function(){
        $('#myfilter').show();
        $('#myfilter-name').focus();
    })
    $('#close-myfilter').click(function(){
        $('#myfilter').hide();
    })
    $("#myfilter-name").bind("input propertychange",function(event){
        let txt=get_txt_value($(this).val(),$('#myfilter-name2').val())
        if(txt.length>0){
            last=event.timeStamp;
            setTimeout(function(){
                if(last-event.timeStamp==0)
                {
                    refresh_filter(txt);
                }
            },500);
        }else{
           last=event.timeStamp;
           setTimeout(function(){
                refresh_filter(txt);
           },500);
        }
    });
    $("#myfilter-name2").bind("input propertychange",function(event){
        let txt=get_txt_value($('#myfilter-name').val(),$(this).val())
        if(txt.length>0){
            last2=event.timeStamp;
            setTimeout(function(){
                if(last2-event.timeStamp==0)
                {
                    refresh_filter(txt);
                }
            },500);
        }else{
           last2=event.timeStamp;
           setTimeout(function(){
                refresh_filter(txt);
           },500);
        }
    });
}

function fill_dropdown(item){
    let span_ele=$(item).children('span');
    $("#label-filter").text(span_ele.text());
    $("#label-filter").attr("data-pk",span_ele.attr("data-pk"));
    if(span_ele.attr("data-pk")==0){
        labelFilterValue="";
    }else{
        labelFilterValue=span_ele.text();
    }
    nodesView.refresh();
}

function init_label_list(){
    let label_list=$('#label-list');
    label_list.empty();
    let ele='<li onclick="fill_dropdown(this)"><span class="dropdown-item" data-pk=0>全部</span></li>';
    label_list.append($(ele));
}

function init_dropdown(){
    $.ajax({
        url:'/mdict/getlabels/',
        contentType:'json',
        type:'GET',
        success:function(data){
            let data_list=$.parseJSON(data);
            let label_list=$('#label-list');
            init_label_list();
            for(let i=0;i<data_list.length;i++){
                var ele='<li onclick="fill_dropdown(this)"><span class="dropdown-item" data-pk='+data_list[i][0]+'>'+data_list[i][1]+'</span></li>';
                label_list.append($(ele));
            }
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

$(document).ready(function(){
    init_event();
    init_dropdown();
    create_network();
});
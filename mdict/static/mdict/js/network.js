var iframe_script=`
<script src="/static/jquery/jquery.min.js"></script>
<script>

var nodes=null;
var edges=null;

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

function create_network(){
    $.ajax({
        url:'/mdict/getnodes/',
        contentType:'json',
        type:'GET',
        success:function(data){
            var pdata=$.parseJSON(data);
            var node_list=pdata['nodes'];
            var edge_list=pdata['edges'];
            nodes = new vis.DataSet(node_list);
            edges = new vis.DataSet(edge_list);
            var ndata={'nodes':nodes,'edges':edges};
            var network=set_data(ndata);
            init_events(network);
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

function init_events(network){
    network.on("click",function(params){
        var ids = params.nodes;
        var clickedNodes = nodes.get(ids);
        if(clickedNodes.length>0){
            var label=clickedNodes[0]["label"];
            get_entry(label);
        }
    })
    $("#home").click(function(){
        window.location.href="/";
    });
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

$(document).ready(function(){
    create_network();
});
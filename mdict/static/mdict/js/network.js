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

function create_network(){
    $.ajax({
        url:'/mdict/getdigraph/',
        contentType:'json',
        type:'GET',
        success:function(data){
            var pdata=$.parseJSON(data);
            var node_list=pdata['nodes'];
            var edge_list=pdata['edges'];
            var nodes = new vis.DataSet(node_list);
            var edges = new vis.DataSet(edge_list);
            var ndata={'nodes':nodes,'edges':edges};
            var network=set_data(ndata);
            init_events(network,nodes);
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function create_entry(entry,html){
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
            var html='<style>html,body{height:320px;}</style><script src=\"/static/mdict/iframe-resizer/js/iframeResizer.contentWindow.min.js\"></script>'+tcontent+iframe_script;
            //设置iframe的html和body高度，否则前一次的高度会影响后一次。
            create_entry(tentry,html);
        },
        error:function(jqXHR,textStatus,errorThrown){
            alert(jqXHR.responseText);
        },
    })
}

function init_events(network,nodes){
    network.on("click",function(params){
        var ids = params.nodes;
        var clickedNodes = nodes.get(ids);
        if(clickedNodes.length>0){
            var label=clickedNodes[0]["label"];
            get_entry(label);
        }
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
            initiallyActive: false,
            addNode: true,
            addEdge: true,
            //editNode: undefined,//editNode应该是回调函数
            editEdge: true,
            deleteNode: true,
            deleteEdge: true,
        },
        layout: {
            improvedLayout:improved_layout,
        }
    };
    return new vis.Network(container, data, options);
}

$(document).ready(function(){
    create_network();
});
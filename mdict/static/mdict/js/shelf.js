var script=`
<script src='/static/mdict/iframe-resizer/js/iframeResizer.contentWindow.min.js'></script>
`;

function start_modal(obj){
    var dic_pk=$(obj).attr('data-pk');
    var dic_name=$(obj).attr('data-name');
    get_header($("#modal-shelf-dic .modal-body"),dic_pk,dic_name);
}


function get_items(container){
	$.ajax({
		url:"/mdict/mdictlist/",
		contentType:'json',
		type:'GET',
		success:function(data){
			var d=$.parseJSON(data);
			for(var i=0;i<d.length;i++){
				var dic_name=d[i]["dic_name"];
				var dic_file=d[i]["dic_file"];
				var dic_icon=d[i]["dic_icon"];
				var dic_pror=d[i]["dic_pror"];
				var dic_pk=d[i]["dic_pk"];
				var dic_enable=d[i]["dic_enable"];
				var dic_es_enable=d[i]["dic_es_enable"]
				var dic_type=d[i]["dic_type"];

                var s=`
                <div class="col">
                    <div class="card shadow" title="${html_escape(dic_name)}" data-pk=${dic_pk} data-name="${html_escape(dic_name)}" onclick="start_modal(this)">
                        <div class="card-body text-center">
                            <img class="" src="${html_escape(dic_icon,false)}"></img>
                            <div class="card-title"><b class="text-primary">${dic_pror}</b>&nbsp;${html_escape(dic_name)}</div>
                        </div>
                    </div>
                </div>
                `

				container.append(s);
			}
		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function get_header(container, dic_pk, dic_name){
	container.empty();

	$('#modal-shelf-dic-title').text(dic_name);

	var data={"dic_pk":dic_pk};
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
            var modal_shelf_dic = new bootstrap.Modal(document.getElementById('modal-shelf-dic'), {});
            modal_shelf_dic.show();

		},
		error:function(jqXHR,textStatus,errorThrown){
			alert(jqXHR.responseText);
		},
	});
}

function shelf_dic_btn(type){
    var dic_pk=$("#modal-shelf-dic").attr('data-pk');
    if(type==0){
        window.open('/mdict/dic/'+dic_pk+'/');
    }else if(type==1){
        window.open('/mdict/esdic/'+dic_pk+'/');
    }else{
        window.open('/admin/mdict/mdictdic/'+dic_pk+'/');
    }
}
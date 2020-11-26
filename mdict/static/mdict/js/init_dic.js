var t_scroll=[]

var dic_first=true;//是否是打开网页的第一次调用

var dic_back=true;//方向是否向后

var dic_search=true//是搜索还是滚动列表的点击

var dic_entry_nums=30;//滚动列表项的数量

$(function() {
	init_single_dic();
});

function loadmore(obj1,obj2){
//obj1是外层的div，obj2是内层的ul，可以想象成外部高度小的obj1运动，内部高度大的obj2不动，从上向下运动。obj1上边框距离obj2上边框的距离是scrollTop，当scrollTop+obj1高度==obj2高度时，说明滚动到底部。

	var scrollTop = obj1.scrollTop();
	var obj1Height = obj1.height();
	var obj2Height = obj2.height();
	dic_search=false;

	var dic_pk=$("html").attr("data-dic-pk");
	if (obj1Height+scrollTop>=obj2Height-1) {
	//到达底部
	console.log("到达底部");
		dic_back=true;
		p1=$("#display_list").attr("data-end-p1");
		p2=$("#display_list").attr("data-end-p2");
		query_scroll(p1,p2,dic_entry_nums,0,dic_pk);
	}else if(scrollTop==0){
	//到达顶部
	console.log("到达顶部");
		dic_back=false;
		p1=$("#display_list").attr("data-start-p1");
		p2=$("#display_list").attr("data-start-p2");

		if(!(p1==0&&p2==0)){
			query_scroll(p1,p2,dic_entry_nums,0,dic_pk);
		}

	}
}

/*很简单的一个方法，就实现了，你给a赋值的时候，绑定了一个事件，这个事件参数，event你可以自己传入一个函数。这样你以调用给a赋值的方法，set_scroll 就会执行这个绑定的事件*/
var set_scroll = function(_t_scroll,d,event){
	t_scroll=_t_scroll.slice();

    if(event){
       event();
    }
};

/**调用例子*/
var func = function(){
	$("#display_list").empty();
	//len=$("#display_list").children().length;
	$.each(
		t_scroll ,
		function(i,v) {
			$("#display_list").append("<li id='li-"+i+"'>" + html_escape(v[0],false) + "</li>") ;
			$("#li-"+i).attr("data-start",v[1]);
			$("#li-"+i).attr("data-end",v[2]);
		}
	);

	$("#display_list").on("click","li",function(){
		$("#alert-box").empty();
		$("li").each(function(){
			$(this).removeAttr("style");
		});
		$(this).css("background-color","#BBBBBB");
		var li_id=parseInt($(this).attr("id").substring(3));
		$("#display_list").attr("data-clicked",li_id);
		var entry=$(this).text();
		//$("#query").val(entry);//将entry填充到input
		//这里填充的话会导致传入dic的query无法被查询。
		//后面再处理
		var dic_pk=$("html").attr("data-dic-pk");
		var s=$(this).attr("data-start");
		var e=$(this).attr("data-end");

		rotate_item_list={};//清空页面旋转记录

		query_record($("#card-container"),entry,dic_pk,s,e);

	});
}
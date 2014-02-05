// page init
$(function(){

    $(document).keyup(function(e) {
	if (e.keyCode == 27) { bringWallpaper(); }   // esc
    });
    loadAllPosts();
});

var overlay = false;

function bringWallpaper() {
    if (overlay == false) {
	$('body').append('<div id="overlay"></div>');
	overlay=true;
    } else { $('#overlay').remove(); overlay=false; }
}

function loadAllPosts() {
    $("#view-all").click(function(){
	$.ajax({url:"/loadAll/3",success:function(result){
	    $("#arts").append(result);
	    $("#view-all").parent().remove();
	}});
    });
}




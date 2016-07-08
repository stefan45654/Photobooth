// JavaScript Document
function startCountdown(){
myvar =  setInterval(function () {
        secondPlay()
    }, 1200);
   
};

function resetCountdown(){
					var aa = $("ul.secondPlay li.active");
	    $("ul.secondPlay li").removeClass("before");
	    aa.addClass("before").removeClass("active");
       aa = $("ul.secondPlay li").eq(0);
        aa.addClass("active")
            .closest("body")
            .addClass("play");
}

function secondPlay() {
    //$("body").removeClass("play");
     var aa = $("ul.secondPlay li.active");

    if (aa.html() == undefined) {
        aa = $("ul.secondPlay li").eq(0);
        aa.addClass("before")
            .removeClass("active")
            .next("li")
            .addClass("active")
            .closest("body")
            .addClass("play");

    }
    else if (aa.is(":last-child")) {
        
       clearInterval(myvar);
	     //execute('s');
        releaseCamera();
	  //aa = $("ul.secondPlay li").eq(0);
	  //  $("ul.secondPlay li").removeClass("before");
	    //aa.addClass("before").removeClass("active");
      // aa = $("ul.secondPlay li").eq(0);
        //aa.addClass("active")
         //   .closest("body")
         //   .addClass("play");
			
	
    }
    else {
        $("ul.secondPlay li").removeClass("before");
        aa.addClass("before")
            .removeClass("active")
            .next("li")
            .addClass("active")
            .closest("body")
            .addClass("play");
			
  }

}
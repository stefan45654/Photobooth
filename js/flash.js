function flash(){

    $('#flashdiv').show()   //show the hidden div
    .animate({opacity: 1}, 300) 
    .fadeOut(300)
    .css({'opacity': 1});
    
};

$(document).ready(function() {    
                $('#flashdiv').hide(); 
});
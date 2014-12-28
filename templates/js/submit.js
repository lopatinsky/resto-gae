$('body').on( "click", "#update",function(e)
{

  
  var company_title=$('#company_title').val(); 
  var app_title=$('#app_title').val(); 
  
  //schedule 
  
  var weekdays=$("#weekdays").is(':checked') ? 1 : 0;
  var friday=$("#friday").is(':checked') ? 1 : 0;
  var saturday=$("#saturday").is(':checked') ? 1 : 0;
  var sunday=$("#sunday").is(':checked') ? 1 : 0;
  
  
  //working hours 
  var worksheet=new Object(); 
  worksheet.company_title=company_title;
  worksheet.app_title=app_title;
  
  worksheet.schedule=new Array();
 
  if(weekdays==1)
  {     
  		var weekdays_from=$("#weekdays_from").val();
		var weekdays_to=$("#weekdays_to").val();
		
		weekdays_array=[]
	    weekdays_array.days="[1,2,3,4]";
	    weekdays_array.from=weekdays_from;
	    weekdays_array.to=weekdays_to;
	    worksheet.schedule.push(weekdays_array);
  }
  if(friday==1)
  {
  		var friday_from=$("#friday_from").val()
		var friday_to=$("#friday_to").val()
		
		friday_array=[]
		friday_array.days="[5]";
		friday_array.from=friday_from;
		friday_array.to=friday_to;
		worksheet.schedule.push(friday_array);
  }
   if(saturday==1)
  {
  		var saturday_from=$("#saturday_from").val()
		var saturday_to=$("#saturday_to").val()
		
		saturday_array=[]
	    saturday_array.days="[6]";
	    saturday_array.from=saturday_from;
	    saturday_array.to=saturday_to;
	    worksheet.schedule.push(saturday_array);
  }
  
   if(sunday==1)
  {
  		var sunday_from=$("#sunday_from").val()
		var sunday_to=$("#sunday_to").val()
		
		 sunday_array=[]
         sunday_array.days="[7]";
  		 sunday_array.from=sunday_from;
  		 sunday_array.to=sunday_to;
 		 worksheet.schedule.push(sunday_array);
  
  }
  
worksheet.phone=$('#phone').val();
worksheet.email=$('#email').val();
worksheet.site=$('#site').val();
worksheet.about_text=$("#about_text").val();
worksheet.min_amount=$("#min_amount").val();
 
var delivery_cities = []; 
$('#delivery_cities :selected').each(function(i, selected){ 
  delivery_cities[i] = $(selected).text(); 
});
  
worksheet.delivery_cities= delivery_cities.toString();
worksheet.color=$("#color").val();
worksheet.analytics_code=$("#analytics_code").val();

  
  
 var json = JSON.stringify(worksheet);
 console.log(json);
 
 var company_id=$('#company_id').html(); 
  //var company_id=0;
  $.post( "http://rustem-iiko-automation.empatika-resto-test.appspot.com/api/company/create_or_update", { company_info: json,company_id:company_id})
  .done(function( data ) {
  
  	$('#company_id').html(data.id);
	$('#worksheet').submit();
	
  });
  
  
})

function getUrlParameter(sParam)
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) 
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) 
        {
            return sParameterName[1];
        }
    }
}


$(function() {
  
  var id=getUrlParameter('company_id');
  if(id!=undefined)
  {
	 $('#company_id').html(id);
  }
});
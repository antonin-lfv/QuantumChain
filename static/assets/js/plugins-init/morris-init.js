(function($) {
    "use strict"

	var dlabMorris = function(){
		
		var screenWidth = $(window).width();
		
		var setChartWidth = function(){
			if(screenWidth <= 768)
			{
				var chartBlockWidth = 0;
				chartBlockWidth = (screenWidth < 300 )?screenWidth:300;
				jQuery('.morris_chart_height').css('min-width',chartBlockWidth - 31);
			}
		}
		
		var lineChart2 = function(){
			//Area chart
			Morris.Area({
				element: 'line_chart_2',
				data: [{
						period: '2001',
						smartphone: 0,
						windows: 0,
						mac: 0
					}, {
						period: '2002',
						smartphone: 90,
						windows: 60,
						mac: 25
					}, {
						period: '2003',
						smartphone: 40,
						windows: 80,
						mac: 35
					}, {
						period: '2004',
						smartphone: 30,
						windows: 47,
						mac: 17
					}, {
						period: '2005',
						smartphone: 150,
						windows: 40,
						mac: 120
					}, {
						period: '2006',
						smartphone: 25,
						windows: 80,
						mac: 40
					}, {
						period: '2007',
						smartphone: 10,
						windows: 10,
						mac: 10
					}


				],
				xkey: 'period',
				ykeys: ['smartphone', 'windows', 'mac'],
				labels: ['Phone', 'Windows', 'Mac'],
				pointSize: 3,
				fillOpacity: 0,
				pointStrokeColors: ['#EE3C3C', '#ffaa2b', '#0d99ff'],
				behaveLikeLine: true,
				gridLineColor: 'transparent',
				lineWidth: 3,
				hideHover: 'auto',
				lineColors: ['rgb(13,153,255)', 'rgb(0, 171, 197)', '#0d99ff'],
				resize: true

			});
		}

		
		/* Function ============ */
		return {
			init:function(){
				setChartWidth();
				lineChart2();
			},
			
			
			resize:function(){
				screenWidth = $(window).width();
				setChartWidth();
				lineChart2();
			}
		}
		
	}();

	jQuery(document).ready(function(){
		dlabMorris.init();
		//dlabMorris.resize();
	
	});
		
	jQuery(window).on('load',function(){
		//dlabMorris.init();
	});
		
	jQuery( window ).resize(function() {
		//dlabMorris.resize();
		//dlabMorris.init();
	});
   
})(jQuery);
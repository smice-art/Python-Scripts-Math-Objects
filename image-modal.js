window.onload = function () 
{
	//******************************************************
	// Handle "click" event on image that contains "image-popup class.
	//******************************************************
	$(".image-popup").on({
		'click': function() {
			url=$(this).attr("src");
			console.log("image-popup clicked "+url);
			loadImageModal(url);
		}
	});
	
	
	//******************************************************
	// Close popup when the Close button or anything is clicked
	//******************************************************
	$("#image-modal-popup, #image-modal-close-button").on({
		'click': function() {
			closeImagePopup();
		}
	});

	// Set to false if you don't want these
	var waitForImageLoadedEventBeforeDisplaying=true;
	var fadeInImageEnabled=true;

	//******************************************************
	// Callback that is being called when the image is loaded.
	//******************************************************
	function onImageLoaded() 
	{
		// If you need to do anything using the image dimensions, use these values.
		imageWidth	 = this.width;
		imageHeight	 = this.height;
		console.log("imageWidth="+imageWidth+" imageHeight="+imageHeight);

		// Hide loader animation
		$("#image-modal-loader").hide();
		// Display the loaded image.
		$("#image-modal-image").attr("src",this.src);
		if (fadeInImageEnabled)
		{		
			$("#image-modal-image").fadeIn();
		}
	}

	//******************************************************
	// Load the image 
	//******************************************************
	function loadImageModal(url) {
		
		// Use fade animation
		// I use fade animation. If you don't want it, just call jQuery's show() 
		$("#image-modal-popup").fadeIn();

		if (fadeInImageEnabled)
		{
			$("#image-modal-image").hide();
		}
		
		// If enabled, show loading animation while the image is loading in the background
		if (waitForImageLoadedEventBeforeDisplaying)
		{
			// Show loader animation
			$("#image-modal-loader").show();			
			// Blank out previous image (if any(), so that the loader animation, which is set as background-image, becomes visible.
			// Or you can just show a blank popup while the image is loading.
			$("#image-modal-image").attr("src",'');
			// Use temporary image because we want the loader to show while loading. Place the temporary image only after it's loaded.
			var tempImage=new Image();
			tempImage.onload = onImageLoaded;
			tempImage.src=url;
		}
		else
		{
			// Place the image. If there's a previous image, the popup might noticably show the old image 
			// while the new image is being loaded. An old image with different dimensions might also cause abrupt resizing, 
			// to void that, set "waitForImageLoadedEventBeforeDisplaying" to true. 
			$("#image-modal-image").attr("src",url);
			$("#image-modal-image").show();
		}
	}

	//******************************************************
	// Close the popup
	//******************************************************	
	function closeImagePopup() 
	{
		// I use fade animation. If you don't want it, just call jQuery's hide() 
		$("#image-modal-popup").fadeOut();
	}
}
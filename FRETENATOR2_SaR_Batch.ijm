dir1 = getDirectory("Choose Source Directory ");

dir2 = getDirectory("Choose Destination Directory ");
list = getFileList(dir1);
setBatchMode(true);
for (i=0; i<list.length; i++) {
	showProgress(i+1, list.length);
	open(dir1+list[i]);
	run("FRETENATOR2_SaR_Headless.py");
	
	for (j=0;j<nImages;j++) {
	        selectImage(j+1);
	        title = getTitle;
	        //print(title);
	        //ids[i]=getImageID;
	
	        saveAs("tiff", dir2+title);
	};	
	run("Close All");
	

}

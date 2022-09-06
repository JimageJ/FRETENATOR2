dir1 = getDirectory("Choose Source Directory ");

dir2 = getDirectory("Choose Destination Directory ");
list = getFileList(dir1);
//setBatchMode(true);
for (i=0; i<list.length; i++) {
	while(nImages>0){
	run("Close All");
	wait(1000);
	print("wait");
	}
	showProgress(i+1, list.length);
	open(dir1+list[i]);
	run("FRETENATOR2 SaR Headless");
	
	for (j=0;j<nImages;j++) {
	        selectImage(j+1);
	        title = getTitle;
	        //print(title);
	        //ids[i]=getImageID;
	
	        saveAs("tiff", dir2+title);
	};	
	run("Close All");
	selectWindow("Results of "+list[i]);
	saveAs("Results",dir2+"Results of "+list[i]+".csv");
	run("Clear Results");
}

"""
******************************************************************************************
		Written by Jim Rowe, Alexander Jones' lab (SLCU, Cambridge).
								Started: 2022-08-01		
							 		@BotanicalJim
							james.rowe at slcu.cam.ac.uk
									Version 0.1



******************************************************************************************
"""


# *******************************import libraries*****************************************
from ij 			import IJ, ImageStack, ImagePlus,CompositeImage
from fiji.util.gui 	import GenericDialogPlus
from ij.process 	import ImageProcessor, StackStatistics, ImageConverter, FloatProcessor, ImageConverter
from ij.measure 	import ResultsTable
from array 			import array, zeros
from java.lang 		import Thread
from ij.plugin 		import Slicer
import pickle
from os.path 		import exists


# *******************************functions************************************************


def globalBackSub(labelGFX, quantGFX, otherGFX):
	"""Requires a labelGFX image, the quantGFX to be quantified (also the output) and, one sacrificial otherGFX images"""
	results=ResultsTable()
	clij2.statisticsOfBackgroundAndLabelledPixels(quantGFX, labelGFX, results)
	IJ.log(str(results.getValue("MEAN_INTENSITY",0)))
	clij2.addImageAndScalar(quantGFX, otherGFX, -results.getValue("MEAN_INTENSITY",0))
	clij2.copy(otherGFX,quantGFX)
	return quantGFX
	
	
def createSubtractionLabels(labelGFX, gfx2, outputGFX):
	"""Requires a labelGFX image, two sacrificial otherGFX images, one of which will be the output"""
	clij2.dilateLabels(labelGFX, gfx2 , 4)
	clij2.subtractImages(gfx2, labelGFX, outputGFX)
	return outputGFX
	
	
def localLabelBackSub(dilatedLabelGFX, labelGFX, quantGFX, otherGFX1, otherGFX2):
	"""Requires a dilatedlabelGFX image, labelGFX, a quantGFX image, and two sacrificial otherGFX images"""
	results4=ResultsTable()
	clij2.statisticsOfBackgroundAndLabelledPixels(quantGFX, dilatedLabelGFX, results4)
	intensities=results4.getColumn(12)
	fp= FloatProcessor(len(intensities), 1, intensities, None)
	intensitiesImp= ImagePlus("IntensitiesImp", fp)
	intGFX=clij2.push(intensitiesImp)
	clij2.replaceIntensities(labelGFX, intGFX, otherGFX1)
	intGFX.close()
	clij2.subtractImages(quantGFX, otherGFX1, otherGFX2)
	clij2.copy(otherGFX2, quantGFX)
	return quantGFX
			
							
def extractChannel(imp, nChannel, nFrame):
	"""extract a channel from the image, at a given frame returning a new imagePlus labelled with the channel name"""
	stack = imp.getImageStack()
	ch=ImageStack(imp.width, imp.height)
	for i in range(imp.getNSlices()):
		index = imp.getStackIndex(nChannel, i, nFrame)
		ch.addSlice(str(i), stack.getProcessor(index))
	imp3 = ImagePlus("Channel " + str(nChannel), ch).duplicate()
	stats =StackStatistics(imp3) 
	IJ.setMinAndMax(imp3, stats.min, stats.max)
	return imp3

def extractFrame(imp, nFrame):
	"""extract a frame from the image, returning a new 16 bit imagePlus labelled with the channel name"""
	stack = imp.getImageStack()
	fr=ImageStack(imp.width, imp.height)
	for i in range(1, imp.getNSlices() + 1):
		for nChannel in range(1, imp.getNChannels()+1):
			index = imp.getStackIndex(nChannel, i, nFrame)
			fr.addSlice(str(i), stack.getProcessor(index))
	imp3 = ImagePlus("Frame " + str(nFrame), fr).duplicate()
	imp3.setDimensions(imp.getNChannels(), imp.getNSlices(), 1)
	comp = CompositeImage(imp3, CompositeImage.COMPOSITE)  
	comp.show()
	return comp

def errorDialog(message):
	"""Outputs a given error for end users"""
	gd = GenericDialogPlus("Error")
	gd.addMessage(message)
	gd.showDialog()
	return
	
def concatStacks(masterStack, impToAdd):
	"""takes an IMP and adds it to a stack, returning the concatenated stack"""
	impToAddStack=impToAdd.getImageStack()
	for i in xrange(1, impToAdd.getNSlices()+1):
		try:	
			masterStack.addSlice(impToAddStack.getProcessor(i))	
		except: print "FAILED To addto stack for: "+ impToAdd.getTitle() +" " + str(i)	
	return masterStack

def previewDialog(imp, options):
	"""Generates the settings dialog and preview window, which live updates dependent on chosen settings"""
	gd = GenericDialogPlus("FRETENATOR2: 2FRET2FURIOUSLY")
	#unpack default settings
	segmentChannel, donorChannel, acceptorChannel, acceptorChannel2, thresholdMethod, maxIntensity, gaussianSigma, largeDoGSigma, DoG,  manualSegment, manualThreshold, makeNearProj, dilation, sizeExclude, minSize, maxSize, watershed, backsubVal, pixelByPixel, saveSettings =options
	#create a list of the channels in the provided imagePlus
	types = []
	for i in xrange(1, imp.getNChannels()+1):
		types.append(str(i))
		
	gd.addMessage("""Channel choices:""")
	#user can pick which channel to base the segmentation on
	if (segmentChannel<= len(types) and
		donorChannel<= len(types) and
		acceptorChannel<= len(types) and
		acceptorChannel2<= len(types)):
		gd.addChoice("Segmentation channel", types, str(segmentChannel))
		gd.addChoice("Donor channel (denominator)", types, str(donorChannel))
		gd.addChoice("Acceptor (FRET) channel (numerator)", types, str(acceptorChannel))
		gd.addChoice("Acceptor channel", types, str(acceptorChannel2))
	else:
		if len(types)>2:
			gd.addChoice("Segmentation channel", types, types[2])
			gd.addChoice("Donor channel (denominator)", types, types[0])
			gd.addChoice("Acceptor (FRET) channel (numerator)", types, types[1])
			gd.addChoice("Acceptor channel", types, types[2])
			#print('YAY')
		else:
			gd.addChoice("Segmentation channel", types, types[-1])
			gd.addChoice("Donor channel (denominator)", types, types[0])
			gd.addChoice("Acceptor (FRET) channel (numerator)", types, types[-1])
			gd.addChoice("Acceptor channel", types, types[-1])
	gd.addMessage("""Segmentation settings:""")
	methods=["Otsu","Default", "Huang", "Intermodes", "IsoData", "IJ_IsoData", "Li", "MaxEntropy", "Mean", "MinError", "Minimum", "Moments", "Percentile", "RenyiEntropy", "Shanbhag", "Triangle", "Yen"]
	
	gd.addCheckbox("Use difference of Gaussian instead of Gaussian?", DoG)
	gd.addSlider("Small DoG/Gaussian sigma", 0.5, 10, gaussianSigma, 0.1)
	gd.addSlider("Large DoG sigma", 0.5, 20, largeDoGSigma,0.1)
	gd.setModal(False)
	gd.addChoice("Autosegmentation method", methods, thresholdMethod)
	gd.addCheckbox("Manually set threshold? ", manualSegment)
	gd.addSlider("Manual threshold", 10, 65534, manualThreshold, 1)
	
	dilationOptions=["0", "1", "2","3", "4", "5", "6"]
	
	gd.addChoice("Dilation?", dilationOptions, str(dilation))
	gd.addCheckbox("Size exclusion of ROI? ", sizeExclude)
	gd.addSlider("Minimum ROI size", 0, 9999, minSize, 1)
	gd.addSlider("Maximum ROI size", 1, 10000, maxSize, 1)
	gd.addCheckbox("Watershed object splitting? ", watershed)
	
	
	gd.addMessage("""Analysis settings:""")
	backsubOpts=["Off", "Local label based", "Global mean"]
	intensities=["254", "4094", "65534"]
	gd.addChoice("Max intensity (saturation removal)", intensities, str(maxIntensity))
	gd.addChoice("Background subtraction", backsubOpts, backsubOpts[backsubVal])
	gd.addCheckbox("""Use pixel by pixel analysis? (for non-punctate sensors)""", pixelByPixel)
	gd.addCheckbox("Create nearest point projection with outlines? ", makeNearProj)
	gd.addCheckbox("Save segmentation and analysis settings? ", False)
	gd.addMessage("""Please cite
	
	Rowe, J. H, Rizza, A., Jones A. M. (2021) Quantifying phytohormones
	in vivo with FRET biosensors and the FRETENATOR analysis toolset
	https://doi.org/10.1007/978-1-0716-2297-1_17
	
	Rowe, JH., et al., Next-generation ABACUS biosensors reveal cellular
	ABA dynamics driving root growth at low aerial humidity
	""")
	gd.setLocation(0,0)
	gd.showDialog()

		
	cal = imp.getCalibration()
	pixelAspect=(cal.pixelDepth/cal.pixelWidth)
	
	originalTitle=imp1.getTitle()
	
	choices=gd.getChoices()
	sliders=gd.getSliders()
	checkboxes=gd.getCheckboxes()		
	segmentChannel=int(choices.get(0).getSelectedItem())
	donorChannel=int(choices.get(1).getSelectedItem())
	acceptorChannel=int(choices.get(2).getSelectedItem())
	acceptorChannel2=int(choices.get(3).getSelectedItem())
	thresholdMethod=choices.get(4).getSelectedItem()
	dilation=int(choices.get(5).getSelectedItem())
	maxIntensity=int(choices.get(6).getSelectedItem())
	backSub= choices.get(7).getSelectedItem()
	
	gaussianSigma=sliders.get(0).getValue()/10.0
	largeDoGSigma = gd.sliders.get(1).getValue()/10.0
	manualThreshold=gd.sliders.get(2).getValue()
	minSize = gd.sliders.get(3).getValue()
	maxSize = gd.sliders.get(4).getValue()
	
	
	

	DoG = gd.checkboxes.get(0).getState()
	manualSegment = gd.checkboxes.get(1).getState()
	sizeExclude=gd.checkboxes.get(2).getState()
	watershed = gd.checkboxes.get(3).getState()
	#backSub = gd.checkboxes.get(4).getState()
	pixelByPixel = gd.checkboxes.get(4).getState()
	#print dir(gd.sliders.get(5))
	#print maxSize
	
	segmentChannelOld=segmentChannel
	thresholdMethodOld=thresholdMethod
	maxIntensityOld=maxIntensity
	gaussianSigmaOld=gaussianSigma
	largeDoGSigmaOld= largeDoGSigma
	DoGOld=DoG
	manualSegmentOld= manualSegment
	manualThresholdOld=manualThreshold
	dilationOld=dilation
	sizeExcludeOld=sizeExclude
	minSizeOld=minSize
	maxSizeOld=maxSize
	watershedOld=watershed
	clij2.clear()
	
	segmentImp=extractChannel(imp1, segmentChannel, 0)

	try:
		gfx1=clij2.push(segmentImp)
		gfx2=clij2.create(gfx1)
		gfx3=clij2.create(gfx1)
		gfx4=clij2.create(gfx1)
		gfx5=clij2.create(gfx1)
		gfx7=clij2.create([imp.getWidth(), imp.getHeight()])
	except:	
		try:
		
			Thread.sleep(500)
			print("Succeeded to sending to graphics card on the second time...")
			gfx1=clij2.push(segmentImp)
			gfx2=clij2.create(gfx1)
			gfx3=clij2.create(gfx1)
			gfx4=clij2.create(gfx1)
			gfx5=clij2.create(gfx1)
			gfx7=clij2.create([imp.getWidth(), imp.getHeight()])
		except:
			errorDialog("""Could not send image to graphics card, it may be too large!
		
			Easy solutions: Try	processing as 8-bit, cropping or scaling the image, or
			select a different CLIJ2 GPU.

			This issue is often intermittent, so trying again may also work! 

			See the "Big Images on x graphics cards' notes at:
			https://clij2.github.io/clij2-docs/troubleshooting for more solutions
			
			"""	+ str(clij2.reportMemory()) )


	gfx1,gfx2,gfx3,gfx4,gfx5 = segment(gfx1,gfx2,gfx3,gfx4,gfx5, gaussianSigma, thresholdMethod, maxIntensity, largeDoGSigma, pixelAspect, originalTitle, DoG,  manualSegment, manualThreshold, dilation, sizeExclude, minSize, maxSize, watershed)
	clij2.maximumZProjection(gfx5, gfx7)

	labelPrevImp= clij2.pull(gfx7)
	IJ.setMinAndMax(labelPrevImp, 0,clij2.getMaximumOfAllPixels(gfx7))
	labelPrevImp.setTitle("Preview segmentation")
	labelPrevImp.show()
	
	IJ.run("glasbey_inverted")
	
	while ((not gd.wasCanceled()) and not (gd.wasOKed())):
		

		segmentChannel=int(choices.get(0).getSelectedItem())
		donorChannel=int(choices.get(1).getSelectedItem())
		acceptorChannel=int(choices.get(2).getSelectedItem())
		acceptorChannel2=int(choices.get(3).getSelectedItem())
		thresholdMethod=choices.get(4).getSelectedItem()
		dilation=int(choices.get(5).getSelectedItem())
		maxIntensity=int(choices.get(6).getSelectedItem())
		
		gaussianSigma=sliders.get(0).getValue()/10.0
		largeDoGSigma = gd.sliders.get(1).getValue()/10.0
		manualThreshold=gd.sliders.get(2).getValue()
		minSize = gd.sliders.get(3).getValue()
		maxSize = gd.sliders.get(4).getValue()
		
		
		
		
		DoG = gd.checkboxes.get(0).getState()
		manualSegment = gd.checkboxes.get(1).getState()
		sizeExclude=gd.checkboxes.get(2).getState()
		watershed = gd.checkboxes.get(3).getState()
		#backSub = gd.checkboxes.get(4).getState()
		pixelByPixel = gd.checkboxes.get(4).getState()
	
		if (segmentChannelOld !=segmentChannel or
			thresholdMethodOld !=thresholdMethod or
			maxIntensityOld !=maxIntensity or
			gaussianSigmaOld !=gaussianSigma or
			largeDoGSigmaOld != largeDoGSigma or
			DoGOld !=DoG or
			manualSegmentOld != manualSegment or
			manualThresholdOld !=manualThreshold or
			dilation != dilationOld or
			sizeExcludeOld!=sizeExclude or
			minSizeOld!=minSize or
			maxSizeOld!=maxSize or
			watershedOld!=watershed
			):
				if minSizeOld!=minSize:
					if minSize>=maxSize:
						maxSize=minSize+1
						gd.sliders.get(5).setValue(maxSize)
				if maxSizeOld!=maxSize:
					if minSize>=maxSize:
						minSize=maxSize-1
						gd.sliders.get(4).setValue(minSize)
				if segmentChannelOld!=segmentChannel:
						clij2.clear()
						print('eh')
						segmentImp=extractChannel(imp1, segmentChannel, 0)
						gfx1=clij2.push(segmentImp)
						gfx2=clij2.create(gfx1)
						gfx3=clij2.create(gfx1)
						gfx4=clij2.create(gfx1)
						gfx5=clij2.create(gfx1)
						gfx7=clij2.create([imp.getWidth(), imp.getHeight()])
				gfx1,gfx2,gfx3,gfx4,gfx5 = segment(gfx1,gfx2,gfx3,gfx4,gfx5, gaussianSigma, thresholdMethod, maxIntensity, largeDoGSigma, pixelAspect, originalTitle, DoG, manualSegment, manualThreshold, dilation,sizeExclude, minSize, maxSize, watershed)
				clij2.maximumZProjection(gfx5, gfx7)
				labelPrevImp.close()
				labelPrevImp= clij2.pull(gfx7)
				IJ.setMinAndMax(labelPrevImp, 0,clij2.getMaximumOfAllPixels(gfx7))
				labelPrevImp.setTitle("Preview segmentation")
				labelPrevImp.show()
				
				IJ.run("glasbey_inverted")
		
		segmentChannelOld=segmentChannel
		thresholdMethodOld=thresholdMethod
		maxIntensityOld=maxIntensity
		gaussianSigmaOld=gaussianSigma
		largeDoGSigmaOld = largeDoGSigma
		DoGOld=DoG
		manualSegmentOld= manualSegment
		manualThresholdOld=manualThreshold
		dilationOld=dilation
		sizeExcludeOld=sizeExclude
		minSizeOld=minSize
		maxSizeOld=maxSize
		watershedOld=watershed
		Thread.sleep(200)
	if gd.wasCanceled():
		clij2.clear()
		IJ.exit()
	
	labelPrevImp.close()
	makeNearProj = gd.checkboxes.get(5).getState()
	backSub= choices.get(7).getSelectedItem()
	saveSettings = gd.checkboxes.get(6).getState()
	backsubVal=0
	if backSub=="Local label based":
		backsubVal=1
	if backSub=="Global mean":
		backsubVal=2
	return segmentChannel, donorChannel, acceptorChannel, acceptorChannel2, thresholdMethod, maxIntensity, gaussianSigma, largeDoGSigma, DoG,  manualSegment, manualThreshold, makeNearProj, dilation, sizeExclude, minSize, maxSize, watershed, backsubVal, pixelByPixel, saveSettings
	
def segment(gfx1,gfx2,gfx3,gfx4,gfx5, gaussianSigma, thresholdMethod, maxIntensity, largeDoGSigma, pixelAspect, originalTitle, DoG,  manualSegment, manualThreshold, dilation, sizeExclude, minSize, maxSize, watershed):
	"""Segmentation based on user settings"""
	# DoG filter for background normalised segmentation. NB. Kernel is Z-normalised to pixel aspect ratio
	if DoG == True :	
		clij2.differenceOfGaussian3D(gfx1, gfx2, gaussianSigma, gaussianSigma, 1+(gaussianSigma-1)/pixelAspect, largeDoGSigma, largeDoGSigma,largeDoGSigma/pixelAspect)
	else:
		clij2.gaussianBlur3D(gfx1, gfx2, gaussianSigma,gaussianSigma, 1+(gaussianSigma-1)/pixelAspect)

	if manualSegment == True :
		clij2.threshold(gfx2, gfx3, manualThreshold)
	else:
		#auto threshold and watershed to seed the object splitting
		clij2.automaticThreshold(gfx2, gfx3, thresholdMethod)

	if watershed:
		clij2.watershed(gfx3,gfx2)
	else:
		clij2.copy(gfx3,gfx2)
	
	# add watershed to original threshold, and then use this to generate a binary image of any ROI lost in watershed process
	clij2.addImages(gfx2, gfx3, gfx5)
	clij2.floodFillDiamond(gfx5, gfx4, 1, 2)
	clij2.replaceIntensity(gfx4, gfx5, 2, 0)
	
	#label watershed image
	clij2.connectedComponentsLabelingDiamond(gfx2, gfx4)

	#dilate all the labeled watershed ROI out (only onto zero labeled pixels), then multiply this by original binary map, to get labeled ROI
	clij2.dilateLabels(gfx4, gfx2, 6)

	clij2.multiplyImages(gfx2,gfx3, gfx4)
	
	#label the missed ROI then add on the largest value from the other labelled image (so they can be combined)
	watershedLabelMax =clij2.getMaximumOfAllPixels(gfx4)
	clij2.connectedComponentsLabelingDiamond(gfx5, gfx2)
	clij2.addImageAndScalar(gfx2, gfx5, (1 + watershedLabelMax))
	
	#delete the background and combine the two images
	clij2.replaceIntensity(gfx5, gfx2,(1 + watershedLabelMax), 0)
	clij2.maximumImages(gfx4, gfx2, gfx5)
	
	#remove labeled objects that are too big or too small
	if sizeExclude:
		clij2.excludeLabelsOutsideSizeRange(gfx5, gfx4, minSize, maxSize)
		clij2.copy(gfx4, gfx5)
		
	#dilate images
	if dilation:
		clij2.dilateLabels(gfx5, gfx4, dilation)
		clij2.copy(gfx4, gfx5)
	#gfx3 = threshold channel, gfx5 = label image, gfx1=original image, gfx2 & gfx4  are junk
	clij2.closeIndexGapsInLabelMap(gfx5,gfx4)
	return gfx1,gfx2,gfx3,gfx5, gfx4

def fretCalculations(imp1, nFrame, donorChannel, acceptorChannel, acceptorChannel2, table, gfx1, gfx2, gfx3, gfx4, gfx5, originalTitle, backSub, pixelByPixel):
	"""Perform FRET calculations (Sorry! Complex function!)"""
	
	#Extract appropriate channels
	donorImp=extractChannel(imp1, donorChannel, nFrame)
	acceptorImp=extractChannel(imp1, acceptorChannel, nFrame)
	acceptorImp2=extractChannel(imp1, acceptorChannel2, nFrame)
	
	#push donor and acceptor channels to gpu threshold
	gfx4=clij2.push(donorImp)
	gfx5=clij2.push(acceptorImp)
	gfx6=clij2.create(gfx5)

	#thresholds to create a mask to remove saturated pixels from donor and acceptor images	
	clij2.threshold(gfx4,gfx2, maxIntensity)
	clij2.binarySubtract(gfx3, gfx2, gfx6)
	clij2.threshold(gfx5,gfx2, maxIntensity)
	clij2.binarySubtract(gfx6, gfx2, gfx3)
	clij2.threshold(gfx3,gfx6, 0.5)
	
	#Apply appropriate background subtraction if required (must be after the saturated pixel removal). NB. Local label uses more GPU memory, which may be a limiting factor on some computers
	if backSub==1:
		gfx7=clij2.create(gfx1)
		gfx3=createSubtractionLabels(gfx1, gfx2, gfx3)
		gfx4=localLabelBackSub(gfx3, gfx1, gfx4, gfx2, gfx7)
		gfx5=localLabelBackSub(gfx3, gfx1, gfx5, gfx2, gfx7)
	if backSub==2:
		gfx4=globalBackSub(gfx1, gfx4, gfx2)
		gfx5=globalBackSub(gfx1, gfx5, gfx2)
	
	
	#Mask to remove the saturated pixels
	#donor is gfx2, acceptor FRET is gfx4, segment channel (acceptor normal) is gfx6, gfx3 is triple threshold
	clij2.mask(gfx4,gfx6, gfx2)
	clij2.mask(gfx5,gfx6, gfx4)
			
	#NB have to push the acceptor image now...
	gfx6=clij2.push(acceptorImp2)
	if backSub==1:
		gfx6=localLabelBackSub(gfx3, gfx1, gfx6, gfx5, gfx7)
		gfx7.close()
	if backSub==2:
		gfx6=globalBackSub(gfx1, gfx6, gfx5)

	#extract the intensity of each nucleus for each channel
	results=ResultsTable()
	clij2.statisticsOfBackgroundAndLabelledPixels(gfx2, gfx1, results)
	donorChIntensity=results.getColumn(13)
	results2=ResultsTable()
	clij2.statisticsOfBackgroundAndLabelledPixels(gfx4, gfx1, results2)
	acceptorChIntensity=results2.getColumn(13)
	results3=ResultsTable()
	clij2.statisticsOfBackgroundAndLabelledPixels(gfx6, gfx1, results3)
	
	#calculate the fret ratios, removing any ROI with intensity of zero
	FRET =[]
	
	for i in xrange(len(acceptorChIntensity)):
		if (acceptorChIntensity[i]>0) and (donorChIntensity[i]>0):
			#don't write in the zeros to the results
			FRET.append((1000*acceptorChIntensity[i]/donorChIntensity[i]))
			table.incrementCounter()
			#frame, label and ER
			table.addValue("Frame (Time)", nFrame)
			table.addValue("Label", i)
			table.addValue("Emission ratio", acceptorChIntensity[i]/donorChIntensity[i])

			#mean emission
			table.addValue("Mean donor emission", results.getValue("MEAN_INTENSITY",i))
			table.addValue("Mean acceptor emission (FRET)", results2.getValue("MEAN_INTENSITY",i))
			table.addValue("Mean acceptor emission", results3.getValue("MEAN_INTENSITY",i))
			
			#sum emission
			table.addValue("Sum donor emission", donorChIntensity[i])
			table.addValue("Sum acceptor emission (FRET)", acceptorChIntensity[i])
			table.addValue("Sum acceptor emission", results3.getValue("SUM_INTENSITY",i))
			#shape and location descriptors
			table.addValue("Volume", cal.pixelWidth * cal.pixelHeight * cal.pixelDepth * results.getValue("PIXEL_COUNT",i))
			table.addValue("Pixel count", results.getValue("PIXEL_COUNT",i))
			table.addValue("x", cal.pixelWidth*results.getValue("CENTROID_X",i))
			table.addValue("y", cal.pixelHeight*results.getValue("CENTROID_Y",i))
			table.addValue("z", cal.pixelDepth*results.getValue("CENTROID_Z",i))
			
			#File name for traceability 
			table.addValue("File name", originalTitle)
		else:
			#must write in the zeros as this array is used to generate the map of emission ratios
			FRET.append(0)
			
	table.show("Results of " + originalTitle)
	#export label image
	labelImp = clij2.pull(gfx1)
	if pixelByPixel==0:
		#write all the emission ratios to an array, push to an GFX image, use this to map emission ratios
		FRET[0]=0
		FRETarray= array( "f", FRET)
		fp= FloatProcessor(len(FRET), 1, FRETarray, None)
		FRETImp= ImagePlus("FRETImp", fp)
		gfx4=clij2.push(FRETImp)
		clij2.replaceIntensities(gfx1, gfx4, gfx5)
		maxProj=clij2.create(gfx5.getWidth(), gfx5.getHeight(), 1)
		clij2.maximumZProjection(gfx5, maxProj)
		
		
		#pull the images
		FRETimp2=clij2.pull(gfx5)
		FRETProjImp=clij2.pull(maxProj)
		
	else:
		
		#donor is gfx2, acceptor FRET is gfx4, segment channel (acceptor normal) is gfx6, threshold image:gfx3
		#blur the acceptor and donor channels, then remask to prevent NaN/infinite values after division
		clij2.gaussianBlur3D(gfx4, gfx5, 1.1, 1.1, 1.1)
		clij2.mask(gfx5, gfx1, gfx4)
		clij2.gaussianBlur3D(gfx2, gfx5, 1.1, 1.1, 1.1)
		clij2.mask(gfx5, gfx1, gfx2)
		
		#create Z sum projected donor and acceptor images for Z-proj ratio calc -> may replace with a different technique later
		donorSum=clij2.create(gfx4.getWidth(), gfx4.getHeight(), 1)
		acceptorFSum=clij2.create(gfx4.getWidth(), gfx4.getHeight(), 1)
		clij2.sumZProjection(gfx2, donorSum)
		clij2.sumZProjection(gfx4, acceptorFSum)
		
		#Divide Z proj Acceptor by Z proj Donor and pull image
		maxProj=clij2.create(gfx4.getWidth(), gfx4.getHeight(), 1)
		clij2.divideImages(acceptorFSum, donorSum, maxProj)
		clij2.multiplyImageAndScalar(maxProj, donorSum,1000)
		FRETProjImp=clij2.pull(donorSum)
		
		#pull acceptor and donor stacks to convert to 32 bit
		acceptorImp=clij2.pull(gfx4)
		donorImp=clij2.pull(gfx2)
		ImageConverter(acceptorImp).convertToGray32()
		ImageConverter(donorImp).convertToGray32()
		
		#clean up GPU memory
		clij2.clear()
		
		#push 32bit images and perform ratio calc
		gfx4=clij2.push(acceptorImp)
		gfx2=clij2.push(donorImp)
		gfx1=clij2.create(gfx2.getDimensions(), clij2.Float)
		clij2.divideImages(gfx4, gfx2, gfx1)
		clij2.multiplyImageAndScalar(gfx1, gfx2,1000)
		#pull ratio stack
		FRETimp2=clij2.pull(gfx1)

	#clean up
	clij2.clear()
	donorImp.close()
	acceptorImp.close()
	acceptorImp2.close()
	
	return table, FRETimp2, FRETProjImp, labelImp
	
	
def nearestZProject(imp1):
	relicedImp=Slicer().reslice(imp1)
	relicedStack=relicedImp.getStack()
	width=imp1.getWidth()
	height=imp1.getHeight()
	depth=imp1.getNSlices()
	
	topPixels=zeros('f', width * height)  
	
	stack2=ImageStack( width, height)
	for i in range(1,relicedImp.getNSlices()):
		pixels= relicedStack.getPixels(i)
		for x in xrange(width):
			for pixel in xrange(x, x+width*(depth-1),width):
				#after finding the first pixel above the threshold value, add the value to the list
				if pixels[pixel] != 0:
				
					topPixels[i*width+x]=pixels[pixel]
					#break from looping the y when 1st threshold pixel is found is met -> increases speed drastically! Otherwise need an if statement every loop...
					break
	
	ip2=FloatProcessor(width, height, topPixels, None)
	imp2=ImagePlus("Nearest point proj",ip2)
	imp3= imp2.resize(imp2.getWidth()*2, imp2.getHeight()*2, 'none')
	return imp3



def outline(imp3, originalTitle):
	
	
	#clij implementation -thicker lines
	"""
	src=clij2.push(imp3)
	dst=clij2.create(src)
	dst2=clij2.create(src)
	clij2.detectLabelEdges(src,dst)
	clij2.binaryNot(dst,dst2)
	clij2.multiplyImages(src, dst2, dst)
	imp4=clij2.pull(dst)
	imp4.show()
	clij2.clear()
	"""
	
	imp2=imp3.duplicate()
	stack1=imp3.getStack()
	width=imp3.getWidth()
	height=imp3.getHeight()
	stack2=ImageStack(width, height)
	pixlist=[]
	
	for i in range(imp3.getNSlices()):
		pixlist=[]
		pixels1=stack1.getPixels(i+1)
		#if pixel is different to the pixel to the left or above, set it to 0
		pixels2=map(lambda j: pixels1[j] if pixels1[j]-pixels1[j-1]==0 and pixels1[j]-pixels1[j-width]==0 else 0, xrange(len(pixels1)))
		processor=FloatProcessor(width, height, pixels2, None)
		stack2.addSlice(processor)
	imp2=ImagePlus("Nearest point emission ratios of "+ originalTitle, stack2)
	imp2.show()
	return imp2


# *****************************body of code starts****************************************


#give install instructions for CLIJ if not installed

try: 
	from net.haesleinhuepf.clij2 import CLIJ2

except:
	errorDialog("""This plugin requires clij2 to function. 
	
	To install please follow these instructions: 
	
	1. Click Help>Update> Manage update sites
	2. Make sure the "clij2" update site is selected.
	3. Click Close> Apply changes.
	4. Close and reopen ImageJ""")


clij2 = CLIJ2.getInstance()
clij2.clear()


#get the current image
imp1= IJ.getImage()

#define inputs (to be put in a dialog if I automate) 
if exists('FRETENATOR2SegSettings.pckl'):
	print('exists')
	sf=file('FRETENATOR2SegSettings.pckl', 'rb')
	options=pickle.load(sf)
	sf.close()
	print(options)
else:
	options=(3, 1, 2, 3, 'Otsu', 65534, 0.8, 4.0, True, False, 3000, True, 0, False, 10, 10000, True, 0, False, True)
	


#get the pixel aspect for use in zscaling kernels for filters
cal = imp1.getCalibration()
pixelAspect=(cal.pixelDepth/cal.pixelWidth)
originalTitle=imp1.getTitle()



IJ.log(originalTitle +" settings:")
IJ.log("segmentChannel, donorChannel, acceptorChannel, acceptorChannel2, thresholdMethod, maxIntensity, gaussianSigma, largeDoGSigma, DoG, manualSegment, manualThreshold, makeNearProj, dilation, sizeExclude, minSize, maxSize, watershed, backSub:")
IJ.log(str(options))

segmentChannel, donorChannel, acceptorChannel, acceptorChannel2, thresholdMethod, maxIntensity, gaussianSigma, largeDoGSigma, DoG,  manualSegment, manualThreshold, makeNearProj, dilation, sizeExclude, minSize, maxSize, watershed, backSub, pixelByPixel, saveSettings =options
if saveSettings==1:
	sf=file('FRETENATOR2SegSettings.pckl', 'wb')
	pickle.dump(options, sf)
	sf.close()
if pixelByPixel==1:
	makeNearProj =0
totalFrames=imp1.getNFrames() +1

#table is the final results table
table = ResultsTable()

clij2 = CLIJ2.getInstance()
clij2.clear()



conThresholdStack=ImageStack(imp1.width, imp1.height)
conFRETImp2Stack=ImageStack(imp1.width, imp1.height)
conFRETProjImpStack=ImageStack(imp1.width, imp1.height)
conlabelImpStack=ImageStack(imp1.width, imp1.height)
conNearZStack=ImageStack(imp1.width*2, imp1.height*2)
for nFrame in xrange(1, totalFrames):
	clij2.clear()
	segmentImp=extractChannel(imp1, segmentChannel, nFrame)
	gfx1=clij2.push(segmentImp)
	gfx2=clij2.create(gfx1)
	gfx3=clij2.create(gfx1)
	gfx4=clij2.create(gfx1)
	gfx5=clij2.create(gfx1)
	gfx1,gfx2,gfx3,gfx4,gfx5 = segment(gfx1,gfx2,gfx3,gfx4,gfx5, gaussianSigma, thresholdMethod,maxIntensity, largeDoGSigma, pixelAspect, originalTitle, DoG,manualSegment, manualThreshold, dilation,sizeExclude, minSize, maxSize, watershed)
	
	thresholdImp = clij2.pull(gfx3)
	IJ.setMinAndMax(thresholdImp, 0,1)
	thresholdImp.setCalibration(cal)
	thresholdImp.setTitle("Binary mask of "+originalTitle)

	table, FRETimp2, FRETProjImp, labelImp=fretCalculations(imp1, nFrame, donorChannel, acceptorChannel, acceptorChannel2, table, gfx5, gfx2, gfx3, gfx4, gfx1, originalTitle,backSub, pixelByPixel)

	if makeNearProj == True:
		nearZImp = nearestZProject(FRETimp2)
		conNearZStack=concatStacks(conNearZStack,nearZImp)
		nearZImp.close()
		
	#add the images to concatenated stacks
	conThresholdStack = concatStacks(conThresholdStack, thresholdImp)
	conFRETImp2Stack=concatStacks(conFRETImp2Stack, FRETimp2)
	conFRETProjImpStack=concatStacks(conFRETProjImpStack, FRETProjImp)
	conlabelImpStack=concatStacks(conlabelImpStack, labelImp)
	
	thresholdImp.close()
	FRETimp2.close()
	FRETProjImp.close()
	labelImp.close()

#Show the images and make the images pretty... I should have put in a function`

conThresholdImp= ImagePlus( "Threshold image for "+ originalTitle, conThresholdStack)
conThresholdImp.setDimensions(1,  imp1.getNSlices(), imp1.getNFrames())
IJ.setMinAndMax(conThresholdImp, 0,1)
conThresholdImp.setCalibration(cal)
conThresholdImp = CompositeImage(conThresholdImp, CompositeImage.COMPOSITE)
conThresholdImp.show()


conFRETImp2 = ImagePlus( "Emission ratios X1000 of "+ originalTitle, conFRETImp2Stack)
conFRETImp2.setDimensions(1, imp1.getNSlices(), imp1.getNFrames())
conFRETImp2.setCalibration(cal)
stats=StackStatistics(conFRETImp2)
conFRETImp2 = CompositeImage(conFRETImp2, CompositeImage.COMPOSITE)  
IJ.setMinAndMax(conFRETImp2, 1000, 4000)
conFRETImp2.show()
IJ.run("16_colors")


conFRETProjImp= ImagePlus( "Max Z  projection of emission ratios X1000 of "+ originalTitle, conFRETProjImpStack)
conFRETProjImp.setDimensions(1, 1, imp1.getNFrames())
conFRETProjImp.setCalibration(cal)
stats=StackStatistics(conFRETProjImp)
IJ.setMinAndMax(conFRETProjImp, 1000, 4000)
conFRETProjImp = CompositeImage(conFRETProjImp, CompositeImage.COMPOSITE)  
conFRETProjImp.show()
IJ.run("16_colors")

conlabelImp= ImagePlus("Label map "+ originalTitle, conlabelImpStack)
conlabelImp.setDimensions(1, imp1.getNSlices(), imp1.getNFrames())
conlabelImp.setCalibration(cal)
stats=StackStatistics(conlabelImp)
conlabelImp = CompositeImage(conlabelImp, CompositeImage.COMPOSITE)  
IJ.setMinAndMax(conlabelImp, 0,stats.max)
conlabelImp.show()
IJ.run("glasbey_inverted")

if makeNearProj == True:
	conNearZImp=ImagePlus("Nearest Z proj of  ratios of"+ originalTitle, conNearZStack)
	nearZImpOutlines = outline(conNearZImp,originalTitle)
	IJ.setMinAndMax(nearZImpOutlines, 1000, 4000)
	nearZImpOutlines.show()
	IJ.run("16_colors")

clij2.clear()

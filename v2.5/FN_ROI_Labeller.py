"""
******************************************************************************************
	Written by Jim Rowe (U of Sheffield) in collaboration with Alexander Jones (SLCU, Cambridge)
								Started: 2021-01-30	
							 		@BotanicalJim
							james.rowe at sheffield.ac.uk
									Version 2

******************************************************************************************
"""


# *******************************import libraries*****************************************

from ij 					import IJ, ImagePlus, ImageStack, CompositeImage
from fiji.util.gui 			import GenericDialogPlus
from ij 					import WindowManager as WM  
from java.awt.event 		import ActionListener,AdjustmentListener, ItemListener
from net.haesleinhuepf.clijx import CLIJx
from ij.process 			import ImageProcessor, ShortProcessor,StackStatistics, ImageConverter
from java.awt  				import GridLayout, Font, Color
from ij.measure 			import ResultsTable
from ij.gui 				import Overlay
from ij.gui 				import TextRoi, Roi
from java.lang 				import Thread
from datetime 				import datetime  
import os
import json


from sys import path
from java.lang.System import getProperty

path.append(getProperty('fiji.dir') + '\\plugins\\FRETENATOR2\\v2.5')
import FN2_Apply_Weka_to_labels as clsfr
import FN2_Label_ROI_map_to_training_data as trningdata
import FN2_Train_Weka_label_classifier as trnclsfr

# *******************************classes*****************************************



class previewLabelerAndListeners(ActionListener, AdjustmentListener):


	'''Class which unique function is to handle the button clics'''
	def __init__(self,imp1, slider1,slider2,slider3, slider4, gd):
		self.height=imp2.getHeight()
		self.width=imp2.getWidth()
		self.depth=imp2.getStackSize()
		
		self.stats=StackStatistics(imp2)
		self.src=clijx.push(imp2)
		self.cal = imp2.getCalibration()
		self.size=int(self.stats.max)+1
		#print 'size' , int(self.stats.max)
		self.labelValues=[1]*int(self.size)
		self.labelValues[0]=0
				
		self.nucleiLabels=range(self.size)
		self.results=ResultsTable()
		
		self.renderPreview(1)
		#self.results.show("results")
		self.labelDict={0:[0], 1: sorted(self.nucleiLabels[1:]), 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[]}
		
		self.identifiers=[]
		self.xs=[]
		self.ys=[]
		self.zs=[]
		self.bbz=[]
		self.bbze=[]
		self.vol=[]		

		self.errors=[]
		
		for i in range(int(self.size)):
			try:
				
				self.xs.append(int(self.results.getValue("CENTROID_X",i)))
				self.ys.append(int(self.results.getValue("CENTROID_Y",i)))
				self.zs.append(int(self.results.getValue("CENTROID_Z",i)))
				self.bbz.append(self.results.getValue("BOUNDING_BOX_Z",i)+1)
				self.bbze.append(self.results.getValue("BOUNDING_BOX_END_Z",i)+1)
				self.identifiers.append(self.results.getValue("IDENTIFIER", i))
				self.vol.append(self.results.getValue("PIXEL_COUNT", i))
			except:
				print 'error'+str( i)
				self.identifiers.append(self.results.getValue("IDENTIFIER", i))
				self.xs.append(-100)
				self.ys.append(-100)
				self.zs.append(-100)
				self.bbz.append(1)
				self.bbze.append(1)
				self.vol.append(0)
				self.errors.append(i)
				
		
		self.nucLoc= map(lambda i : self.ys[i] * width +self.xs[i], range(len(self.xs)))

		"""labelPreviewImp -  label image preview; maxZPreviewImp - maxZ label preview; maxYPreviewImp - maxY label preview"""
	
		self.slider1=slider1
		self.slider2=slider2
		self.slider3=slider3
		self.slider4=slider4
		self.gd=gd
		self.current=self.labelPreviewImp.getCurrentSlice()
		
		
		
	def renderPreview(self,runStats):
		try:
			self.labelPreviewImp.close()
			self.maxZPreviewImp.close()
			self.maxYPreviewImp.close()
		except:
			print "imps already closed"
		
		
		fp= ShortProcessor(len(self.labelValues), 1, self.labelValues, None)
		labelerImp= ImagePlus("labeler", fp)
		src2=clijx.push(labelerImp)
		dst=clijx.create(self.src)
		labelerImp.close()
		
		clijx.replaceIntensities(self.src, src2, dst)
		self.labelPreviewImp=clijx.pull(dst)
		previewDisplaySettings(self.labelPreviewImp, "label preview", 100, self.cal)
		
		try:
			self.labelPreviewImp.setSlice(self.current)
		except:
			pass
		if runStats:
			clijx.statisticsOfBackgroundAndLabelledPixels(dst, self.src, self.results)
		dst2=clijx.create(width, height, 1)
		clijx.maximumZProjection(dst,dst2)
		self.maxZPreviewImp=clijx.pull(dst2)
		previewDisplaySettings(self.maxZPreviewImp, "maxZ label preview", 50, self.cal)
		
		dst3=clijx.create(width, depth, 1)
		clijx.maximumYProjection(dst,dst3)
		self.maxYPreviewImp=clijx.pull(dst3)
		previewDisplaySettings(self.maxYPreviewImp, "maxY label preview", 50, self.cal)
		
		
		dst3.close()
		dst.close()
		dst2.close()
		src2.close()


		labelWindow = self.labelPreviewImp.getWindow()
		x=labelWindow.getLocation().x
		y=labelWindow.getLocation().y
		
		maxZPreviewWindow=self.maxZPreviewImp.getWindow()
		maxZPreviewWindow.setLocation(x, y+height+50)
		maxYPreviewWindow=self.maxYPreviewImp.getWindow()
		maxYPreviewWindow.setLocation(x+width/2, y+height+50)
		print labelWindow
	def actionPerformed(self, event): 
		"""event: actionlistener does stuff on buttonpress"""


		Source = event.getSource() # returns the Button object
		self.current=self.labelPreviewImp.getCurrentSlice()
		
		if Source.label == "Set top":
			self.top = self.labelPreviewImp.getCurrentSlice()
			self.bottom = self.slider2.getValue()
			self.slider1.setValue(int(self.top))
			if (self.bottom < self.top) :
				self.bottom=self.top
				self.slider2.setValue(int(self.top))
			return
		
			
		if Source.label == "Set bottom":
			self.top = self.slider1.getValue()
			self.bottom = self.labelPreviewImp.getCurrentSlice()
			self.slider2.setValue(int(self.bottom))
			if self.bottom < self.top:
				self.slider1.setValue(int(self.bottom))
				self.top = self.bottom
				print "B"
			return
			
		if Source.label == "Whole stack":
			self.top = 1
			self.bottom = depth
			self.slider1.setValue(int(self.top))
			self.slider2.setValue(int(self.bottom))
			return
			
		if Source.label == "Just slice":
			print "current slice"
			self.top = self.labelPreviewImp.getCurrentSlice()
			self.bottom = self.labelPreviewImp.getCurrentSlice()
			self.slider2.setValue(int(self.top))
			self.slider1.setValue(int(self.bottom))
			return
		if Source.label == "Use pretrained classifier":
		
			labelFilePath ,	modelFilePath, headersFilePath=clsfr.fileSelectDialog()
			rt=clsfr.createResultsTable(imp2,self.src)
			
			with open(headersFilePath, 'r') as config_file:
			    columns = json.load(config_file)
			rtheadingsList = rt.getColumnHeadings().split()
			columnChoices = []
			
			for i in range(len(columns)):
				if columns[i] == True:
					columnChoices.append(i)
			#print columnChoices
			rt2= clsfr.filteredResultsTable(rt, columnChoices)
			clijx.applyWekaToTable(rt2, 'LABEL_ID', modelFilePath)
			rt2.show('test')
			labeledrois=rt2.getColumn("LABEL_ID")
			labeledrois.insert(0,0)
			self.labelDict={0:[],1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[], 11:[]}
			for i,v in enumerate(labeledrois):
				self.labelDict[v].append(i)
			for key in self.labelDict:
				for value in self.labelDict[int(key)]:
					self.labelValues[value]=int(key)	
			print self.labelDict
			print self.labelValues
			self.src=clijx.push(imp2)
			self.renderPreview(0)
			return		
		if Source.label == "Use existing classified image":
			ROIimageName= fileSelectDialog()
			print(ROIimageName)
			ROIimp= WM.getImage(ROIimageName)
			self.labelDict=importROIImage(ROIimp, self.src)
			for key in self.labelDict:
				for value in self.labelDict[int(key)]:
					self.labelValues[value]=int(key)	
			self.renderPreview(0)
			return
		if Source.label == "Train classifier from this image":
			print 'doooo it'
			rtc2 = trningdata.createTrainingResultsTable(imp2, self.labelPreviewImp)
			rtc2.show('test')
			
			filePath=trnclsfr.folderSelectDialog()

			
			#rt.show("data")
			rtheadingsList = rtc2.getColumnHeadings().split()
			
			columns = [False, False, False, False, False, False, False, True, True, True, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, True, True, True, False, False, False, False, True, True, True, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]

			#columns = [1]*len(rtheadingsList)	
			columnChoices, columns= trnclsfr.chooseColumns(columns, rtheadingsList)
			print columns
			rtc3= trnclsfr.filteredResultsTable(rtc2, columnChoices)
			#rtc3.show('trainingdata')
			#print(len(rtc3.getColumnHeadings().split()))
			
			date= datetime.now().strftime("%Y-%m-%d-%H.%M")
			rtc2.save(filePath + "/" + date + "labels.csv")
			
			clijx.trainWekaFromTable(rtc3, 'LABEL_ID', filePath + "/" + date + " classifier.model", 500, 10,10)
		
			with open(filePath+"/"+date+' classifier_fileheaders.json', 'w') as f:
				#	f.write(str(columns))
				json.dump(columns, f)
			
			self.src=clijx.push(imp2)
			return
		
		if Source.label[:5]=="label":
			[int(s) for s in Source.label.split() if s.isdigit()]
			s=int(s)
			print "s " +str(s) 
			
			#xy position filter pixels
			roi1 = self.labelPreviewImp.getRoi()
			selectedPixels=roi1.getContainedPoints()
			roiPixelLoc= map(lambda i : i.y * width +i.x, selectedPixels)
	
			pixels2=filter(lambda i: self.nucLoc[i] in roiPixelLoc, xrange(len(self.nucLoc)))

			#on first run set self.top and self.bottom to top and bottom of the stack
			try: print self.top
			except:  self.top=1
			try: print self.bottom
			except: self.bottom=self.labelPreviewImp.getNSlices()

			#on first run set self.top and self.bottom to top and bottom of the stack
			try: print self.maxSize
			except:  self.maxSize=10000
			try: print self.minSize
			except: self.minSize=0
			
			choice= self.gd.getChoices().get(0)

			if choice.getSelectedItem()== "Slice":
				top=self.current
				bottom=self.current
			else:
				top=self.top
				bottom=self.bottom
			#z position filter pixels
			pixels2=filter(lambda i :max(self.bbze[i],bottom)-min(top,self.bbz[i]) <= (self.bbze[i]-self.bbz[i])+ (bottom-top),pixels2)
			
			pixels2=filter(lambda i :self.vol[i] <= self.maxSize, pixels2)
			pixels2=filter(lambda i :self.vol[i] >= self.minSize, pixels2)		
			self.nucleiLabels=map(lambda i : i,pixels2)


			
			self.labelDict[s] =self.nucleiLabels+self.labelDict[s]
			self.labelDict[s] =sorted(list(set(self.labelDict[s])))
			
			for key in self.labelDict:
				if key != s :
					self.labelDict[key]=filter(lambda x: x not in self.labelDict[s], self.labelDict[key])
			#print labelDict
			for key in self.labelDict:
				for value in self.labelDict[int(key)]:
					self.labelValues[value]=int(key)
		self.labelValues[0]=0
		self.labelDict[0]=[0]
		for key in self.labelDict.keys()[1:]:
			self.labelDict[key]=filter(lambda x: x != 0, self.labelDict[key])
		self.renderPreview(0)
		
		#except:
		#	print "No roi"
		return
		# Do an action depending on the button clicked
	def adjustmentValueChanged(self, event):  
		""" event: an AdjustmentEvent with data on the state of the scroll bar. """ 

		 #return if the user is still dragging
		 
		if event.getValueIsAdjusting():
			return
		Source = event.getSource()
		
		try: self.slider1=self.gd.getSliders().get(0)
		except:  "huh?"
		try: self.slider2=self.gd.getSliders().get(1)
		except: print "huh?2"
		
		self.top = self.slider1.getValue()
		self.bottom = self.slider2.getValue()

		#make top and bottom sliders autocorrect for each other
		if Source== self.slider1:
			if self.top > self.bottom:
				self.slider2.setValue(int(self.top))
				self.bottom=self.top
				print "A"
		if Source== self.slider2:		
			if self.bottom < self.top:
				self.slider1.setValue(int(self.bottom))
				self.top = self.bottom
				print "B"
				
		
		try: self.slider3=self.gd.getSliders().get(2)
		except: print "huh?"
		try: self.slider4=self.gd.getSliders().get(3)
		except: print "huh?2"
		
		self.minSize = self.slider3.getValue()
		self.maxSize = self.slider4.getValue()

		#make top and bottom sliders autocorrect for each other
		if Source== self.slider3:
			if self.maxSize < self.minSize:
				self.slider4.setValue(int(self.minSize)+1)
				self.minSize=self.maxSize
				print "A"
		if Source== self.slider4:		
			if self.minSize > self.maxSize:
				self.slider3.setValue(int(self.maxSize)-1)
				self.maxSize = self.minSize
				print "B"


# *******************************functions************************************************
def concatStacks(masterStack, impToAdd):
	#takes an IMP and adds it to a stack, returning the concatenated stack
	impToAddStack=impToAdd.getImageStack()
	for i in xrange(1, impToAdd.getNSlices()+1):
		try:	
			masterStack.addSlice(impToAddStack.getProcessor(i))	
		except: print "FAILED To addto stack for: "+ impToAdd.getTitle() +" " + str(i)	
	return masterStack

def errorDialog(message):

	gd = GenericDialogPlus("Error")
	gd.addMessage(message)
	gd.showDialog()
	return

def previewDisplaySettings(image, title, zoom, cal):
	"""Apply wanted settings for previews"""
	ImageConverter.setDoScaling(0)
	ImageConverter(image).convertToGray16()
	image.show()
	IJ.run("glasbey_on_dark")
	IJ.setMinAndMax(image, 0, 255)
	image.setTitle(title)
	image.setCalibration(cal)
	IJ.run("Set... ", "zoom="+str(zoom))


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
	#comp.show()
	return comp
		
def dialog(imp2, labelColorBarImp):
	gd = GenericDialogPlus("ROI labeller")
	categories=11

	#placeholder slider variables so the class can be initiated
	slider1=0
	slider2=0	
	slider3=0
	slider4=0
	test=previewLabelerAndListeners(imp2, slider1,slider2,slider3,slider4, gd)
	
	gd.addMessage("Assign selection to:")
	gd.addMessage("	")
	for i in range(1,categories):
		gd.addButton("label "+str(i), test)
		

	#imp7.close() - causes an error as image needed for the dialog
	
	gd.addMessage("Automatic labelling:")
	gd.addMessage("	")
	gd.addButton("Use pretrained classifier", test)
	gd.addButton("Use existing classified image", test)
	gd.addButton("Train classifier from this image", test)
	gd.addMessage("	")
	
	gd.addMessage("Z labelling controls:")
	gd.addMessage("	")
	gd.addButton("Set top",test)
	gd.addButton("Whole stack",test)
	gd.addButton("Set bottom", test)
	gd.addMessage("	")
	gd.addMessage("			Label colour key:")
	gd.addImage(labelColorBarImp)

	
	gd.addSlider("Top",1, imp2.getStackSize(), 1)
	gd.addSlider("Bottom",1, imp2.getStackSize(),imp2.getStackSize())
	gd.addSlider("Minimum ROI size", 0, 9999, 0, 1)
	gd.addSlider("Maximum ROI size", 1, 10000, 10000, 1)

	slider1=gd.getSliders().get(0)
	slider2=gd.getSliders().get(1)
	test.slider1=slider1
	test.slider2=slider2
	slider3=gd.getSliders().get(2)
	slider4=gd.getSliders().get(3)
	test.slider3=slider3
	test.slider4=slider4
	slider1.addAdjustmentListener(test)  
	slider2.addAdjustmentListener(test)
	slider3.addAdjustmentListener(test)  
	slider4.addAdjustmentListener(test)

	gd.addChoice("Apply labeling to:", ["(Sub)stack", "Slice"], "(Sub)stack")

	
	gd.setLayout(GridLayout(0,2))
	
	gd.setModal(False)
	buttons=gd.getButtons()

	gd.showDialog()


	while ((not gd.wasCanceled()) and not (gd.wasOKed())):
		Thread.sleep(50)
	return test


def selectionDialog(categories,labelColorBarImp):
	gd = GenericDialogPlus("ROI labeller -image picking")
	imps = WM.getImageTitles()
	nonimages=WM.getNonImageTitles()
	
	gd.addChoice("Image to quantify", imps, imps[0])
	try:
		gd.addChoice("FRETENTATOR results table", nonimages, nonimages[0])
		fail=0
	except:
		gd.addMessage("No results table open")
		fail=1
	gd.addImage(labelColorBarImp)
	for i in range(categories):
		gd.addStringField("Label "+str(i) +" name:", "Label "+str(i))

	gd.addChoice("Quantify selected image or add labels to open results table?", ["Image", "Results table"], "Results table")
	
	#quantImp= IJ.getImage(gd.getNextChoice())
	
	
	gd.setModal(False)
	gd.showDialog()
	while ((not gd.wasCanceled()) and not (gd.wasOKed())):
		Thread.sleep(50)


	names=dict()
	
	for i in range(categories):
		names[i]=str(gd.getNextString())
	imageName=gd.getNextChoice()
	if fail==0:	
		resultsName=gd.getNextChoice()
		imageOrTable=gd.getNextChoice()
	else:
		imageOrTable="Image"
		resultsName=0
	return names, imageName, resultsName, imageOrTable

def createLabelColorBar():

	imp7 = ImagePlus("labelColorBar", ShortProcessor(180, 20))
	ip7 = imp7.getProcessor()
	pix=ip7.getPixels()
	n_pixels = len(pix)
	# catch width
	w = imp7.getWidth()
	# create a ramp gradient from left to right
	for i in range(len(pix)):
		pix[i] = int((i % w)/18)+1
		
	# adjust min and max
	ip7.setMinAndMax(0, 255)
	font = Font("SansSerif", Font.PLAIN, 12)
	overlay = Overlay()
	for i in range(len(pix)):
		
		roi = TextRoi(i*18+2, 2, str(i+1), font)
		roi.setStrokeColor(Color.black)
		overlay.add(roi)
		imp7.setOverlay(overlay)
	
	imp7.show()
	IJ.run("glasbey_on_dark")
	imp7=imp7.flatten()

	return imp7

def importROIImage(roiimp, src):
	rt=ResultsTable()
	roigtx2=clijx.push(roiimp)
	clijx.statisticsOfBackgroundAndLabelledPixels(roigtx2,src, rt)
	labeledrois =  rt.getColumn('MEAN_INTENSITY')
	labelDict={0:[],1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[], 11:[]}
	for i,v in enumerate(labeledrois):
		labelDict[v].append(i)
	return labelDict


def fileSelectDialog():
	"""Select roi map"""
	imps = WM.getImageTitles()
	gdFS = GenericDialogPlus("Select ROI map")	
	gdFS.addChoice("ROI map to import", imps, imps[0])
	
	gdFS.showDialog()
	imageName=gdFS.getNextChoice()
	if gdFS.wasCanceled():
		imageName= 0
	return 	imageName

# *****************************body of code starts****************************************
	
if __name__ == "__main__":
		
	
	clijx = CLIJx.getInstance()
	clijx.clear()
	
	imp1=IJ.getImage()
	height=imp1.getHeight()
	width=imp1.getWidth()
	depth=imp1.getStackSize()
	frames=imp1.getNFrames()
	
	
	
	if frames > 1:
		imp2 = extractFrame(imp1, 1)
	else:
		imp2=imp1
	stats=StackStatistics(imp2)
	labelColorBarImp= createLabelColorBar()
	categories=11
	#print dir(WM)
	test = dialog(imp2, labelColorBarImp)
	
	names, imageName, resultsName, imageOrTable = selectionDialog(categories,labelColorBarImp)
	
	test.maxZPreviewImp.close()
	test.maxYPreviewImp.close()
	listOfNames  =["Untracked"]*65535
	
	names[11]='Untracked'
	
	invertedDict=dict()
	labelDict=test.labelDict
	
	
	for key in labelDict.keys():
		
		for value in labelDict[key]:
			if value not in test.errors:
				listOfNames[value]=names[key]
				invertedDict[value]= key
			else:
				listOfNames[value]="Untracked"
				invertedDict[value]= 11
				print 'not in labeldict'
	
	if imageOrTable == "Results table":
		rt = ResultsTable.getResultsTable(resultsName).clone()
	
	else:
		measureImp=WM.getImage(imageName)
		src2=clijx.push(measureImp)
		rt = ResultsTable()
		clijx.statisticsOfBackgroundAndLabelledPixels(src2, test.src, rt)
		src2.close()
		resultsName="Results table"
	
	try:
		labels = rt.getColumn(rt.getColumnIndex('TrackID'))
		frame = rt.getColumn(rt.getColumnIndex('Frame (Time)'))
	except:
		try:
			labels = rt.getColumn(rt.getColumnIndex('Label'))
	
		except:
			labels = rt.getColumn(rt.getColumnIndex('IDENTIFIER'))
	
	for i in range(len(labels)):
		try:
				rt.setValue("Label name", i,listOfNames[int(labels[i])])
				rt.setValue("Label value", i,invertedDict[int(labels[i])])
	
		except: 
			print i, 'eye eye'
	
	rt.show(resultsName+ " with labels")
	clijx.clear()
	labelColorBarImp.close()
	imp1Stats=imp1.getStatistics()
	print imp1Stats.max
	tracked=[11]*int(65535)
	for i,v in enumerate(test.labelValues):
		if value not in test.errors:
			tracked[i]= v
		else:
			tracked[i]= 11
	print test.labelValues
	fp= ShortProcessor(len(tracked), 1,tracked , None)
	
	labelerImp= ImagePlus("labeler", fp)
	src2=clijx.push(labelerImp)
	conLabeledStack=ImageStack(imp1.width, imp1.height)
	
	
	if frames>1:
		for nFrame in range(1,frames+1):
	
			imp3=extractFrame(imp1, nFrame)
			src=clijx.push(imp3)
			dst=clijx.create(src)
			clijx.replaceIntensities(src, src2, dst)
			LabeledImp=clijx.pull(dst)
			conLabeledStack = concatStacks( conLabeledStack, LabeledImp)
		concatLabeledImp= ImagePlus("Labeled "+imageName, conLabeledStack)
		
		ImageConverter.setDoScaling(0)
		ImageConverter(concatLabeledImp).convertToGray16()
		
		IJ.setMinAndMax(concatLabeledImp, 0, 255)
		concatLabeledImp.setCalibration(imp1.getCalibration())
		concatLabeledImp.setDimensions(1, imp1.getNSlices(), imp1.getNFrames())
		concatLabeledImp = CompositeImage(concatLabeledImp, CompositeImage.COMPOSITE)
		concatLabeledImp.show()
		IJ.run("glasbey_on_dark")
		labelerImp.close()
	
	labelColorBarImp.close()

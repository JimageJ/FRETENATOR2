"""
******************************************************************************************
						Written by Jim Rowe (U of Sheffield)
								Started: 2026-02-19	
							 		@BotanicalJim
							james.rowe at sheffield.ac.uk
******************************************************************************************
"""
from ij 					import IJ, ImagePlus, ImageStack, CompositeImage
from ij.process 			import ImageProcessor, FloatProcessor, StackStatistics, ImageConverter
#from ij.process 		import ImageProcessor, FloatProcessor
from ij.measure 		import ResultsTable
from fiji.util.gui	 	import GenericDialogPlus
from ij 				import WindowManager as WM  
#import inspect

from jarray import array
from java.util import ArrayList, Random
from weka.core import SerializationHelper,  Attribute, Instances, DenseInstance
from weka.classifiers.trees import RandomForest

from inra.ijpb.measure 	import IntrinsicVolumes3D
from inra.ijpb.label 	import LabelImages
from inra.ijpb.plugins 	import AnalyzeRegions3D
from inra.ijpb.plugins 	import ParticleAnalysis3DPlugin, BoundingBox3DPlugin, ExtendBordersPlugin
import json
import java.lang.System as System

def errorDialog(message):
	"""Outputs a given error for end users"""
	gd = GenericDialogPlus("Error")
	gd.addMessage(message)
	gd.showDialog()
	return

def graphDistCalc(inputVector,touchMatixgtx):
	"""Creates a graph distance vector from the given vector where 1 is the start point"""
	rt=ResultsTable()
	inputVector.insert(0,0.0)
	GraphDistances=FloatProcessor(len(inputVector),1, inputVector, None)
	GraphDistancesImp= ImagePlus("GraphDistances", GraphDistances)
	
	Graphgtx=clij2.push(GraphDistancesImp)
	newGraphgtx=clij2.create(Graphgtx)
	clij2.copy(Graphgtx,newGraphgtx)
	gtx=clij2.create(Graphgtx)
	# Create a horizontal vector of size N-1
	cropgtx=clij2.create([len(inputVector)-1, 1], clij2.Float)
	
	# Crop starting at X=1, Y=0
	clij2.crop(Graphgtx, cropgtx, 1, 0)
	i=0
	
	# use the maximumOfTouchingNeighbors to expand the network...
	while clij2.getMinimumOfAllPixels(cropgtx)==0:
		i=i+1
		clij2.maximumOfTouchingNeighbors(newGraphgtx, touchMatixgtx, gtx)
		clij2.addImages(gtx, Graphgtx, newGraphgtx)
		clij2.crop(newGraphgtx, cropgtx, 1, 0)
		if i==1000: # Just in case isolated things are passed
			print(clij2.getMinimumOfAllPixels(newGraphgtx))
			break
	#print i
	#rt.show('hmm')
	clij2.pullToResultsTableColumn(newGraphgtx, rt, "placeholder", 0)
	#rt.show('hmm')
	inverseData=rt.getColumn("placeholder")

	#reverse direction of the map
	finalcolumn = map(lambda x: max(inverseData)-x,  inverseData)
	#print(finalcolumn)
	finalcolumn[0]=0.0
	#print(len(finalcolumn))
	#cleanup
	Graphgtx.close()
	newGraphgtx.close()
	gtx.close()
	GraphDistancesImp.close()
	cropgtx.close()
	return finalcolumn




def fileSelectDialog():
	"""Select label map and model"""
	nonimages=WM.getNonImageTitles()
	imps = WM.getImageTitles()
	gd = GenericDialogPlus("Select label map , classifier and header file")
	gd.addFileField("Label map file location (optional)", "")
	if len(nonimages) > 0:
		gd.addChoice('Results table', nonimages, nonimages[0])
		fail=0
	else:
		gd.addMessage("No results table open")
		fail=1
	gd.addFileField("Select classifier.model file", "")
	gd.addFileField("Select classifier_fileheaders.json file", "")
	gd.showDialog()
	
	
	if gd.wasCanceled():

		IJ.exit()
	labelFilePath =gd.getNextString()
	rtName= None
	if len(nonimages) > 0:
		rtName =gd.getNextChoice()
	modelFilePath =gd.getNextString()
	headersFilePath = gd.getNextString()
	print rtName

	return 	labelFilePath ,rtName,	modelFilePath, headersFilePath

def createResultsTable(labelImp, labelgtx, size):
	""" Exctracts all data required for each label in the image and writes to a results table to be used for the ML prediction"""	
	
	#get label stats
	rtc = ResultsTable()
	clij2.statisticsOfLabelledPixels(labelgtx, labelgtx, rtc)
	rtcV = ResultsTable()	
	#create point for graph analysis
	pointsgtx=clij2.create(size, clij2.Float)		
	clij2.reduceLabelsToCentroids(labelgtx, pointsgtx)
	pointListgtx=clij2.create([rtc.size()+1, 3], clij2.Float)
	clij2.labelledSpotsToPointList(pointsgtx, pointListgtx)
	#create vorenoi for graph analysis
	vorenoigtx=clij2.create(labelgtx)
	clij2.extendLabelingViaVoronoi(labelgtx, vorenoigtx)
	clij2.statisticsOfLabelledPixels(vorenoigtx, vorenoigtx, rtcV)

	#get offsets from 'top' surface in each dimension
	
	localvorenoigtx=clij2.create(size, clij2.Float)
	localpointsgtx=clij2.create(size, clij2.Float)
	clij2.copy(pointsgtx, localpointsgtx)
	clij2.copy(vorenoigtx,localvorenoigtx)
	
	#extract z positions to pass into surface mapping function
	
	zpos=rtc.getColumn("CENTROID_Z")
	zops= map(float,  zpos)
	ZminsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx, zpos)
	clij2.flip3D(vorenoigtx, localvorenoigtx, 0,0,1)
	clij2.flip3D(pointsgtx, localpointsgtx,0,0,1)
	zpos= map(lambda x: size[2]-x,  zpos)
	ZmaxsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx, zpos)
	localvorenoigtx.close()
	localpointsgtx.close()

	xpos=rtc.getColumn("CENTROID_X")
	xops= map(float,  xpos)
	localvorenoigtx=clij2.create([size[2],size[1],size[0]], clij2.Float)
	localpointsgtx=clij2.create([size[2],size[1],size[0]], clij2.Float)
	clij2.transposeXZ(vorenoigtx, localvorenoigtx)
	clij2.transposeXZ(pointsgtx, localpointsgtx)
	XminsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx, xpos)

	localvorenoigtx2=clij2.create([size[2],size[1],size[0]], clij2.Float)
	localpointsgtx2=clij2.create([size[2],size[1],size[0]], clij2.Float)
	clij2.flip3D(localvorenoigtx,localvorenoigtx2, 0,0,1)
	clij2.flip3D(localpointsgtx,localpointsgtx2, 0,0,1)
	localvorenoigtx.close()
	localpointsgtx.close()
	xpos= map(lambda x: size[0]-x,  xpos)
	XmaxsurfaceOffset = minSurfaceMapping(localpointsgtx2, localvorenoigtx2, xpos)
	localvorenoigtx2.close()
	localpointsgtx2.close()

	ypos=rtc.getColumn("CENTROID_Y")
	yops= map(float,  xpos)
	
	localvorenoigtx=clij2.create([size[0],size[2],size[1]], clij2.Float)
	localpointsgtx=clij2.create([size[0],size[2],size[1]], clij2.Float)
	clij2.transposeYZ(vorenoigtx, localvorenoigtx)
	clij2.transposeYZ(pointsgtx, localpointsgtx)
	YminsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx, ypos)

	localvorenoigtx2=clij2.create([size[0],size[2],size[1]], clij2.Float)
	localpointsgtx2=clij2.create([size[0],size[2],size[1]], clij2.Float)
	clij2.flip3D(localvorenoigtx,localvorenoigtx2, 0,0,1)
	clij2.flip3D(localpointsgtx,localpointsgtx2, 0,0,1)
	localvorenoigtx.close()
	localpointsgtx.close()
	ypos= map(lambda x: size[1]-x,  ypos)
	
	YmaxsurfaceOffset = minSurfaceMapping(localpointsgtx2, localvorenoigtx2,ypos)
	localvorenoigtx2.close()
	localpointsgtx2.close()
	
	#Generate touching and distance matrices
	touchMatixgtx=clij2.create([rtc.size()+1,rtc.size()+1], clij2.Float)
	clij2.generateTouchMatrix(vorenoigtx, touchMatixgtx)
	distanceMatixgtx=clij2.create([rtc.size()+1,rtc.size()+1], clij2.Float)
	clij2.generateDistanceMatrix(pointListgtx,pointListgtx, distanceMatixgtx)
	rtcG=ResultsTable()	
	
	#extract graph theory parameters and wrtie them to the rtG resultstable

	neighbourCountGTX=clij2.create(rtc.size()+1,1, 1)
	clij2.countTouchingNeighbors(touchMatixgtx, neighbourCountGTX)
	clij2.pullToResultsTableColumn(neighbourCountGTX, rtcG, "TOUCHING_NEIGHBORS", 0)
	
	neighbourDistGTX=clij2.create(rtc.size()+1,1, 1)
	clij2.averageDistanceOfTouchingNeighbors(distanceMatixgtx,touchMatixgtx, neighbourDistGTX)
	clij2.pullToResultsTableColumn(neighbourDistGTX, rtcG, "AV_TOUCH_DISTANCE", 0)	
	clij2.maximumDistanceOfTouchingNeighbors (distanceMatixgtx,touchMatixgtx, neighbourDistGTX)
	clij2.pullToResultsTableColumn(neighbourDistGTX, rtcG, "MAX_TOUCH_DISTANCE", 0)	
	clij2.minimumDistanceOfTouchingNeighbors (distanceMatixgtx,touchMatixgtx, neighbourDistGTX)
	clij2.pullToResultsTableColumn(neighbourDistGTX, rtcG, "MIN_TOUCH_DISTANCE", 0)	
	
	# use vorenoi to work out which ROI are closest to each surface
		
	minz=rtcV.getColumn('BOUNDING_BOX_Z')
	maxz=rtcV.getColumn('BOUNDING_BOX_END_Z')
	minx=rtcV.getColumn('BOUNDING_BOX_X')
	maxx=rtcV.getColumn('BOUNDING_BOX_END_X')
	miny=rtcV.getColumn('BOUNDING_BOX_Y')
	maxy=rtcV.getColumn('BOUNDING_BOX_END_Y')
	 
	minZV= map(lambda x: x == float(min(minz)),  minz)
	maxZV= map(lambda x: x == float(max(maxz)),  maxz)
	
	minXV= map(lambda x: x == float(min(minx)),  minx)
	maxXV= map(lambda x: x == float(max(maxx)),  maxx)
	
	minYV= map(lambda x: x == float(min(miny)),  miny)
	maxYV= map(lambda x: x == float(max(maxy)),  maxy)
	
	graphZmin=graphDistCalc(minZV,touchMatixgtx)
	graphZmax=graphDistCalc(maxZV,touchMatixgtx)
	
	graphXmin=graphDistCalc(minXV,touchMatixgtx)
	graphXmax=graphDistCalc(maxXV,touchMatixgtx)
	
	graphYmin=graphDistCalc(minYV,touchMatixgtx)
	graphYmax=graphDistCalc(maxYV,touchMatixgtx)
	
		
	rtcG.deleteRow(0)
	
	headings=rtc.getColumnHeadings()
	headingList=headings.split()
	
	#get morpholib stats
		
	PA3d = ParticleAnalysis3DPlugin()
	morphResults = PA3d.process(labelImp)
	morphColumnNames = morphResults.getColumnHeadings().split()
	
	#combine data tables and display the training data file
	rtc2= ResultsTable()
	for j in range(rtc.size()):
		rtc2.addRow()
		for i in range(len(headingList)-1):
			rtc2.addValue(headingList[i], rtc.getColumn(i)[j])
		for i in range(len(morphColumnNames)-1):
			rtc2.addValue(morphColumnNames[i+1].upper().replace(".", "_"),morphResults.getColumn(i)[j])
		rtc2.addValue('VORONOI_X_MIN_TOUCH', minXV[j])
		rtc2.addValue('VORONOI_X_MAX_TOUCH', maxXV[j])
		
		rtc2.addValue('VORONOI_Y_MIN_TOUCH', minYV[j])
		rtc2.addValue('VORONOI_Y_MAX_TOUCH', maxYV[j])

		rtc2.addValue('VORONOI_Z_MIN_TOUCH', minZV[j])
		rtc2.addValue('VORONOI_Z_MAX_TOUCH', maxZV[j])
		
		rtc2.addValue('GRAPH_DIST_TO_X0', graphXmin[j+1])
		rtc2.addValue('GRAPH_DIST_TO_XMAX', graphXmax[j+1])
		
		rtc2.addValue('GRAPH_DIST_TO_Y0', graphYmin[j+1])
		rtc2.addValue('GRAPH_DIST_TO_YMAX', graphYmax[j+1])
		
		rtc2.addValue('GRAPH_DIST_TO_Z0', graphZmin[j+1])
		rtc2.addValue('GRAPH_DIST_TO_ZMAX', graphZmax[j+1])
		rtc2.addValue('XMIN_SURFACE_OFFSET', XminsurfaceOffset[j])
		rtc2.addValue('XMAX_SURFACE_OFFSET', XmaxsurfaceOffset[j])
		rtc2.addValue('YMIN_SURFACE_OFFSET', YminsurfaceOffset[j])
		rtc2.addValue('YMAX_SURFACE_OFFSET', YmaxsurfaceOffset[j])
		rtc2.addValue('ZMIN_SURFACE_OFFSET', ZminsurfaceOffset[j])
		rtc2.addValue('ZMAX_SURFACE_OFFSET', ZmaxsurfaceOffset[j])
		
		rtc2.addValue("VORENOI_NEIGHBORS", rtcG.getColumn( "TOUCHING_NEIGHBORS")[j])	
		rtc2.addValue("VOR_AV_TOUCH_DISTANCE", rtcG.getColumn( "AV_TOUCH_DISTANCE")[j])	
		rtc2.addValue("VOR_MAX_TOUCH_DISTANCE", rtcG.getColumn( "MAX_TOUCH_DISTANCE")[j])	
		rtc2.addValue("VOR_MIN_TOUCH_DISTANCE", rtcG.getColumn( "MIN_TOUCH_DISTANCE")[j])	
		
		rtc2.addValue('LABEL_ID', 11)

	touchMatixgtx.close()
	distanceMatixgtx.close()
	neighbourCountGTX.close()
	neighbourDistGTX.close()
	heads=rtc2.getColumnHeadings().split()
	vorenoigtx.close()
	pointsgtx.close()
	pointListgtx.close()
	return rtc2

def minSurfaceMapping(localpointsgtx, localvorenoigtx, pos):
	""" WORK OUT WHY REPEATING THIS CAUSES CRASHES"""
	minzTest =map(float, pos)
	minzTest.insert(0,0.0)
	pointListgtx=clij2.create([len(minzTest), 3], clij2.Float)
	clij2.labelledSpotsToPointList(localpointsgtx, pointListgtx)
	
	with open('file.txt', 'a') as outfile:
		outfile.write('\n mid2 \n')
		outfile.write(clij2.reportMemory())
	zPositionsgtx=clij2.create(localvorenoigtx.getDimensions(), clij2.Float)
	
	with open('file.txt', 'a') as outfile:
		outfile.write('\n mid3 \n')
		outfile.write(clij2.reportMemory())
	minzPositionsgtx=clij2.create(zPositionsgtx)

	
	minzTestFP=FloatProcessor(len(minzTest),1, minzTest, None)
	minzTestImp= ImagePlus("minzTestFP", minzTestFP)
	minzTestgtx=clij2.push(minzTestImp)
	
	#generate parametric image of z position, then use a minimum of touching neighbours to identify the top nuceli locally, then blur for a smoother surface
	clij2.generateParametricImage(localvorenoigtx ,minzTestgtx, zPositionsgtx)
	clij2.minimumOfTouchingNeighborsMap(zPositionsgtx, localvorenoigtx, minzPositionsgtx, 2, 0)

	# Flatten vector image: Reassign vector image z position to 0
	pointlist2Dgtx = clij2.create(pointListgtx)
	heightVectorgtx = clij2.create([len(minzTest), 1], clij2.Float)
	clij2.copy(pointListgtx,pointlist2Dgtx)
	clij2.drawBox(pointlist2Dgtx, 0,2,0, len(minzTest), 1 , 1, 0)
	sizel= minzPositionsgtx.getDimensions()
	sizel[2]=1
	
	#extract surface position from the smoothed surface map
	localMinzPosgtx0=clij2.create(sizel, clij2.Float)
	clij2.copySlice(minzPositionsgtx, localMinzPosgtx0, 0)
	minzPositionsgtx.close()
	localMinzPosgtx0Smooth=clij2.create(sizel, clij2.Float)
	clij2.gaussianBlur2D(localMinzPosgtx0,localMinzPosgtx0Smooth,20,20)
	rtcG2=ResultsTable()
	
	clij2.readValuesFromPositions(pointlist2Dgtx, localMinzPosgtx0Smooth, heightVectorgtx)
	clij2.pullToResultsTableColumn(heightVectorgtx, rtcG2, "SURFACE_Z_DEPTH", 0)	
	surfaceZ=rtcG2.getColumn('SURFACE_Z_DEPTH')
	#subtract surface depth from z position to get the Z displacement from the surface
	surfaceOffset= map(lambda x: pos[x]-surfaceZ[x+1],  range(len(pos)))

	pointListgtx.close()
	localMinzPosgtx0.close()
	zPositionsgtx.close()
	minzPositionsgtx.close()
	pointlist2Dgtx.close()
	heightVectorgtx.close()
	localMinzPosgtx0Smooth.close()
	minzTestgtx.close()

	return surfaceOffset

def filteredResultsTable(rtc, columnChoices):
	rtc2=ResultsTable()
	for j in range(rtc.size()):
		rtc2.addRow()
		for i in columnChoices:
			rtc.getColumnHeading(i)
			rtc2.addValue(rtc.getColumnHeading(i), rtc.getColumn(i)[j])
	return rtc2


def concatResultsTable(rt1, rtc):
	
	rtcheadingList = rtc.getColumnHeadings().split()
	rt1headingsList = rt1.getColumnHeadings().split()
	
	#combine both data tables and display the training data file

	for j in range(rtc.size()):
		rt1.addRow()
		for i in range(len(rtcheadingList)):
			rt1.addValue(rtcheadingList[i], rtc.getColumn(i)[j])
	return rt1

def convertTableToInstances(rt2):
	rt2headingsList = rt2.getColumnHeadings().split()
	n_attributes = len(rt2headingsList)
	classList=  [str(i) for i in range(12)]
	
	attributes = ArrayList([Attribute(i) for i in rt2headingsList[:-1]])
	attributes.add(Attribute("class", classList))  
	samples=[]
	sample=[]
	for i in range(rt2.size()):
		sample=[]
		for j in rt2headingsList:
			sample.append(rt2.getValue(j, i))
		samples.append(array(sample,'d'))
	input_data = Instances("test", attributes, len(samples))
	input_data.setClassIndex(len(attributes) -1) # the last one is the class
	for vector in samples:
		input_data.add(DenseInstance(1.0, vector))
	return input_data, attributes

def classify(modelFilePath, input_data, attributes ):
	classifier = SerializationHelper.read(modelFilePath)
	info = Instances("test", attributes, 1) # size of 1
	info.setClassIndex(len(attributes) -1)	
	labels=[0]*(len(input_data)+1)
	i=1
	for vector in input_data:
		vector.setDataset(info)
		class_index = classifier.classifyInstance(vector)
		# print "Classified", vector, "as class", class_index	
		labels[i]=float(class_index)
		i=i+1
	labelsFloat= array(labels, 'f')
	return labelsFloat
def extractFrame(imp, nFrame):
	"""extract a frame from the image, returning a new imagePlus labelled with the channel name"""

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
	
def concatStacks(masterStack, impToAdd):
	#takes an IMP and adds it to a stack, returning the concatenated stack
	impToAddStack=impToAdd.getImageStack()
	for i in xrange(1, impToAdd.getNSlices()+1):
		try:	
			masterStack.addSlice(impToAddStack.getProcessor(i))	
		except: print "FAILED To addto stack for: "+ impToAdd.getTitle() +" " + str(i)	
	return masterStack
	
	
try: 
	from net.haesleinhuepf.clij2 import CLIJ2


except:
	errorDialog("""This plugin requires clij2 to function. 
	
	To install please follow these instructions: 
	
	1. Click Help>Update> Manage update sites
	2. Make sure the "clij" and "clij2" update sites are selected.
	3. Click Close> Apply changes.
	4. Close and reopen ImageJ""")
clij2 = CLIJ2.getInstance()

# *****************************body of code starts****************************************
	
if __name__ == "__main__":
	
	clij2.clear()
	labelFilePath , rtName,	modelFilePath, headersFilePath=fileSelectDialog()
	with open(headersFilePath, 'r') as config_file:
		columns = json.load(config_file)	

	if labelFilePath=="":
		imp1 = IJ.getImage()
	else: imp1 = IJ.openImage(labelFilePath) 

	height=imp1.getHeight()
	width=imp1.getWidth()

	frames=imp1.getNFrames()
	depth=imp1.getStackSize()/frames
	size = [width, height, depth]
	classifier = SerializationHelper.read(modelFilePath)
	conLabeledStack=ImageStack(width, height)
	cal= imp1.getCalibration()
	if rtName != None:
		try:
			rt0 = ResultsTable.getResultsTable(rtName).clone()
		except:
			rt0=ResultsTable()
	p=0	
	for i in range(1,frames+1):
		print i
		if frames > 1:
			labelImp = extractFrame(imp1, i)
			labelImp.setCalibration(cal)
		else:
			labelImp=imp1
			
		labelgtx=clij2.push(labelImp)
		rt=createResultsTable(labelImp,labelgtx, size)		
		clij2.clear()
		System.gc()	
		
		rtheadingsList = rt.getColumnHeadings().split()
		columnChoices = []
		
		for i in range(len(columns)):
			if columns[i] == True:
				columnChoices.append(i)
		rt2= filteredResultsTable(rt, columnChoices)
		input_data, attributes= convertTableToInstances(rt2)
		
		info = Instances("test", attributes, 1) # size of 1
		info.setClassIndex(len(attributes) -1)	
		

		labels=[0]*(len(input_data)+1)
		j=1
		for vector in input_data:
			vector.setDataset(info)
			class_index = classifier.classifyInstance(vector)
			# print "Classified", vector, "as class", class_index	
			labels[j]=float(class_index)
			j=j+1
		labelsFloat= array(labels, 'f')
		for j in range(len(labels)):
			try:
					rt0.setValue("Label value", j+p, labels[j])
			except: 
				print j, 'eye eye'
		p=p+len(labels)


		fp= FloatProcessor(len(labelsFloat), 1, labelsFloat, None)
		newLabelsMappingImp= ImagePlus("IntensitiesImp", fp)
		newLabelsMappingGFX=clij2.push(newLabelsMappingImp)
		otherGFX1=clij2.push(labelImp)
		labelgtx=clij2.push(labelImp)
		clij2.replaceIntensities(labelgtx, newLabelsMappingGFX, otherGFX1)
		newLabelMap=clij2.pull(otherGFX1)
		conLabeledStack = concatStacks(conLabeledStack, newLabelMap)
		newLabelMap.close()
		clij2.clear()
		System.gc()
	ImageConverter.setDoScaling(0)

	concatLabeledImp= ImagePlus("Labeled ROIs", conLabeledStack)
	ImageConverter(concatLabeledImp).convertToGray8()
	concatLabeledImp.setCalibration(imp1.getCalibration())
	concatLabeledImp.setDimensions(1, imp1.getNSlices(), imp1.getNFrames())
	concatLabeledImp = CompositeImage(concatLabeledImp, CompositeImage.COMPOSITE)
	concatLabeledImp.show()
	IJ.run("glasbey_on_dark")
	IJ.setMinAndMax(newLabelMap,0, 255)

	rt0.show('Results with predicted labels')
	
	
	
	

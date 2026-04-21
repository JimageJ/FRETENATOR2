"""
******************************************************************************************
						Written by Jim Rowe (U of Sheffield)
								Started: 2026-02-19	
							 		@BotanicalJim
							james.rowe at sheffield.ac.uk
******************************************************************************************
"""

from ij 				import IJ, ImagePlus
from ij.process 		import ImageProcessor, FloatProcessor
from ij.measure 		import ResultsTable
from fiji.util.gui	 	import GenericDialogPlus
from ij 				import WindowManager as WM  
#import inspect
import array

from inra.ijpb.measure 	import IntrinsicVolumes3D
from inra.ijpb.label 	import LabelImages
from inra.ijpb.plugins 	import AnalyzeRegions3D
from inra.ijpb.plugins 	import ParticleAnalysis3DPlugin, BoundingBox3DPlugin, ExtendBordersPlugin
import json

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
	
	Graphgtx=clijx.push(GraphDistancesImp)
	newGraphgtx=clijx.create(Graphgtx)
	clijx.copy(Graphgtx,newGraphgtx)
	gtx=clijx.create(Graphgtx)
	cropgtx=clijx.create([1,len(inputVector)],clijx.Float)
	#print(cropgtx.getDimensions())
	clijx.crop(Graphgtx, cropgtx, 1,len(inputVector))
	i=0
	
	# use the maximumOfTouchingNeighbors to expand the network, then add on the orginal vector. Floods then maintains the gradient out
	while clijx.getMinimumOfAllPixels(cropgtx)==0:
		i=i+1
		#print(i)
		clijx.maximumOfTouchingNeighbors(newGraphgtx, touchMatixgtx, gtx)
		clijx.addImages(gtx, Graphgtx, newGraphgtx)
		clijx.crop(newGraphgtx, cropgtx, 1,len(inputVector))
		#clijx.pullToResultsTableColumn(newGraphgtx, rt, "TOUCHING_NEIGHBORS"+str(i), 0)
		
		#print(i, clijx.getMeanOfAllPixels(newGraphgtx))
		if i==1000: # Just in case isolated things are passed
			print(clijx.getMinimumOfAllPixels(newGraphgtx))
			break
	#print i
	#rt.show('hmm')
	clijx.pullToResultsTableColumn(newGraphgtx, rt, "placeholder", 0)
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
	return finalcolumn




def fileSelectDialog():
	"""Select label map and model"""
	imps = WM.getImageTitles()
	gd = GenericDialogPlus("Select label map , classifier and header file")
	gd.addFileField("Label map file location (optional)", "")
	gd.addFileField("Select classifier.model file", "")
	gd.addFileField("Select classifier_fileheaders.json file", "")
	gd.showDialog()
	
	
	if gd.wasCanceled():

		IJ.exit()
	labelFilePath =gd.getNextString()
	modelFilePath =gd.getNextString()
	headersFilePath = gd.getNextString()

	return 	labelFilePath ,	modelFilePath, headersFilePath

def createResultsTable(labelImp, labelgtx):
	""" Exctracts all data required for each label in the image and writes to a results table to be used for the ML prediction"""	
	
	#get label stats
	rtc = ResultsTable()
	clijx.statisticsOfLabelledPixels(labelgtx, labelgtx, rtc)
	rtcV = ResultsTable()	
	
	#create point for graph analysis
	pointsgtx=clijx.create(labelgtx.getDimensions(), clijx.Float)		
	clijx.reduceLabelsToCentroids(labelgtx, pointsgtx)
	pointListgtx=clijx.create([rtc.size(), 3], clijx.Float)
	clijx.labelledSpotsToPointList(pointsgtx, pointListgtx)
	
	#create vorenoi for graph analysis
	vorenoigtx=clijx.create(labelgtx)
	clijx.extendLabelingViaVoronoi(labelgtx, vorenoigtx)
	clijx.statisticsOfLabelledPixels(vorenoigtx, vorenoigtx, rtcV)
	size=vorenoigtx.getDimensions()
	
	
	#get offsets from 'top' surface in each dimension
	
	localvorenoigtx=clijx.create(size, vorenoigtx.getNativeType())
	localpointsgtx=clijx.create(size, vorenoigtx.getNativeType())
	ZminsurfaceOffset = minSurfaceMapping(pointsgtx, vorenoigtx)
	clijx.flip(vorenoigtx, localvorenoigtx, 0,0,1)
	clijx.flip(pointsgtx, localpointsgtx,0,0,1)
	ZmaxsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx)
	localvorenoigtx.close()
	localpointsgtx.close()
	
	localvorenoigtx=clijx.create([size[2],size[1],size[0]], vorenoigtx.getNativeType())
	localpointsgtx=clijx.create([size[2],size[1],size[0]], vorenoigtx.getNativeType())
	clijx.transposeXZ(vorenoigtx, localvorenoigtx)
	clijx.transposeXZ(pointsgtx, localpointsgtx)
	XminsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx)
	
	localvorenoigtx2=clijx.create([size[2],size[1],size[0]], vorenoigtx.getNativeType())
	localpointsgtx2=clijx.create([size[2],size[1],size[0]], vorenoigtx.getNativeType())
	clijx.flip(localvorenoigtx,localvorenoigtx2, 0,0,1)
	clijx.flip(localpointsgtx,localpointsgtx2, 0,0,1)
	XmaxsurfaceOffset = minSurfaceMapping(localpointsgtx2, localvorenoigtx2)
	localvorenoigtx.close()
	localpointsgtx.close()
	localvorenoigtx2.close()
	localpointsgtx2.close()
	
	localvorenoigtx=clijx.create([size[0],size[2],size[1]], vorenoigtx.getNativeType())
	localpointsgtx=clijx.create([size[0],size[2],size[1]], vorenoigtx.getNativeType())
	clijx.transposeYZ(vorenoigtx, localvorenoigtx)
	clijx.transposeYZ(pointsgtx, localpointsgtx)
	YminsurfaceOffset = minSurfaceMapping(localpointsgtx, localvorenoigtx)

	localvorenoigtx2=clijx.create([size[0],size[2],size[1]], vorenoigtx.getNativeType())
	localpointsgtx2=clijx.create([size[0],size[2],size[1]], vorenoigtx.getNativeType())
	clijx.flip(localvorenoigtx,localvorenoigtx2, 0,0,1)
	clijx.flip(localpointsgtx,localpointsgtx2, 0,0,1)
	YmaxsurfaceOffset = minSurfaceMapping(localpointsgtx2, localvorenoigtx2)
	localvorenoigtx.close()
	localpointsgtx.close()
	localvorenoigtx2.close()
	localpointsgtx2.close()
	
	#Generate touching and distance matrices
	touchMatixgtx=clijx.create([rtc.size()+1,rtc.size()+1], clijx.Float)
	clijx.generateTouchMatrix(vorenoigtx, touchMatixgtx)
	distanceMatixgtx=clijx.create([rtc.size()+1,rtc.size()+1], clijx.Float)
	clijx.generateDistanceMatrix(pointListgtx,pointListgtx, distanceMatixgtx)
	rtcG=ResultsTable()	
	
	#extract graph theory parameters and wrtie them to the rtG resultstable

	neighbourCountGTX=clijx.create(rtc.size()+1,1, 1)
	clijx.countTouchingNeighbors(touchMatixgtx, neighbourCountGTX)
	clijx.pullToResultsTableColumn(neighbourCountGTX, rtcG, "TOUCHING_NEIGHBORS", 0)
	
	neighbourDistGTX=clijx.create(rtc.size()+1,1, 1)
	clijx.averageDistanceOfTouchingNeighbors(distanceMatixgtx,touchMatixgtx, neighbourDistGTX)
	clijx.pullToResultsTableColumn(neighbourDistGTX, rtcG, "AV_TOUCH_DISTANCE", 0)	
	clijx.maximumDistanceOfTouchingNeighbors (distanceMatixgtx,touchMatixgtx, neighbourDistGTX)
	clijx.pullToResultsTableColumn(neighbourDistGTX, rtcG, "MAX_TOUCH_DISTANCE", 0)	
	clijx.minimumDistanceOfTouchingNeighbors (distanceMatixgtx,touchMatixgtx, neighbourDistGTX)
	clijx.pullToResultsTableColumn(neighbourDistGTX, rtcG, "MIN_TOUCH_DISTANCE", 0)	
	
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
		
		rtc2.addValue('GRAPH_DIST_TO_X0', graphXmin[j])
		rtc2.addValue('GRAPH_DIST_TO_XMAX', graphXmax[j])
		
		rtc2.addValue('GRAPH_DIST_TO_Y0', graphYmin[j])
		rtc2.addValue('GRAPH_DIST_TO_YMAX', graphYmax[j])
		
		rtc2.addValue('GRAPH_DIST_TO_Z0', graphZmin[j])
		rtc2.addValue('GRAPH_DIST_TO_ZMAX', graphZmax[j])
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
		
		#rtc2.addValue('LABEL_ID', rtc.getColumn("MEAN_INTENSITY")[j])
	labelgtx.close()
	touchMatixgtx.close()
	distanceMatixgtx.close()
	neighbourCountGTX.close()
	neighbourDistGTX.close()
	heads=rtc2.getColumnHeadings().split()

	print heads
	print len(heads)
	return rtc2

def minSurfaceMapping(localpointsgtx, localvorenoigtx):

	rtl = ResultsTable()
	clijx.statisticsOfLabelledPixels(localpointsgtx, localpointsgtx, rtl)

	pointListgtx=clijx.create([rtl.size(), 3], clijx.Float)
	clijx.labelledSpotsToPointList(localpointsgtx, pointListgtx)
	
	zPositionsgtx=clijx.create(localvorenoigtx.getDimensions(), clijx.Float)
	
	minzPositionsgtx=clijx.create(zPositionsgtx)
	minzTest=rtl.getColumn("CENTROID_Z")
	minzTest =map(float,minzTest)
	minzTest.insert(0,0.0)
	
	minzTestFP=FloatProcessor(len(minzTest),1, minzTest, None)
	minzTestImp= ImagePlus("minzTestFP", minzTestFP)
	minzTestgtx=clijx.push(minzTestImp)
	
	#generate papametric image of z position, then use a minimum of touching neighbours to identify the top nuceli locally, then blur for a smoother surface
	clijx.generateParametricImage(localvorenoigtx ,minzTestgtx, zPositionsgtx)
	clijx.minimumOfTouchingNeighborsMap(zPositionsgtx, localvorenoigtx, minzPositionsgtx, 2, 0)

	# Flatten vector image: Reassign vector image z position to 0
	pointlist2Dgtx = clijx.create(pointListgtx)
	heightVectorgtx = clijx.create([rtl.size(), 1], clijx.Float)
	clijx.copy(pointListgtx,pointlist2Dgtx)
	clijx.drawBox(pointlist2Dgtx, 0,2,0,rtl.size()+1, 1 , 1, 0)

	
	#extract surface position from the smoothed surface map
	localMinzPosgtx0Smooth=clijx.create(minzPositionsgtx)
	clijx.gaussianBlur2D(minzPositionsgtx,localMinzPosgtx0Smooth,10,10)
	
	rtcG2=ResultsTable()
	clijx.readValuesFromPositions(pointlist2Dgtx,localMinzPosgtx0Smooth,heightVectorgtx)
	clijx.pullToResultsTableColumn(heightVectorgtx, rtcG2, "SURFACE_Z_DEPTH", 0)	
	
	surfaceZ=rtcG2.getColumn('SURFACE_Z_DEPTH')
	zpos=rtl.getColumn('CENTROID_Z')
	#subtract surface depth from z position to get the Z displacement from the surface
	surfaceOffset= map(lambda x: zpos[x]-surfaceZ[x],  range(rtl.size()))


	return surfaceOffset

def filteredResultsTable(rtc, columnChoices):
	rtc2=ResultsTable()
	for j in range(rtc.size()):
		rtc2.addRow()
		for i in columnChoices[:-1]:
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
			#print(j)
	return rt1

try: 
	from net.haesleinhuepf.clijx import CLIJx


except:
	errorDialog("""This plugin requires clijx to function. 
	
	To install please follow these instructions: 
	
	1. Click Help>Update> Manage update sites
	2. Make sure the "clij" and "clijx" update sites are selected.
	3. Click Close> Apply changes.
	4. Close and reopen ImageJ""")
clijx = CLIJx.getInstance()

# *****************************body of code starts****************************************
	
if __name__ == "__main__":
	

	
	clijx.clear()
	labelFilePath ,	modelFilePath, headersFilePath=fileSelectDialog()
	

	if labelFilePath=="":
		labelImp = IJ.getImage()
	else: labelImp = IJ.openImage(labelFilePath) 
	
	labelgtx=clijx.push(labelImp)
	rt=createResultsTable(labelImp,labelgtx)
	
	with open(headersFilePath, 'r') as config_file:
	    columns = json.load(config_file)
	rtheadingsList = rt.getColumnHeadings().split()
	columnChoices = []
	
	for i in range(len(columns)):
		if columns[i] == True:
			columnChoices.append(i)
	#print columnChoices
	rt2= filteredResultsTable(rt, columnChoices)
	clijx.applyWekaToTable(rt2, 'LABEL_ID', modelFilePath)
	rt2.show('Predicted labels')
	
	labels=rt2.getColumn("LABEL_ID")
	#print(len(labels))
	
	labelsFloat=array.array('f', [0]*(len(labels)+1))
	#convert double to float
	for i in range(len(labels)):
		labelsFloat[i+1]=(float(labels[i]))
	
	fp= FloatProcessor(len(labelsFloat), 1, labelsFloat, None)
	newLabelsMappingImp= ImagePlus("IntensitiesImp", fp)
	newLabelsMappingGFX=clijx.push(newLabelsMappingImp)
	otherGFX1=clijx.push(labelImp)
	labelgtx=clijx.push(labelImp)
	clijx.reportMemory()
	clijx.replaceIntensities(labelgtx, newLabelsMappingGFX, otherGFX1)
	newLabelMap=clijx.pull(otherGFX1)
	newLabelMap.show()
	
	IJ.run("glasbey_on_dark")
	IJ.setMinAndMax(newLabelMap,0, 255)
	clijx.clear()
	
	
	
	
	

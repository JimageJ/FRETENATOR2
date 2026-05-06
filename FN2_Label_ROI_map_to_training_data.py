"""
******************************************************************************************
						Written by Jim Rowe (U of Sheffield)
								Started: 2026-02-19	
							 		@BotanicalJim
							james.rowe at sheffield.ac.uk
******************************************************************************************
"""

from ij 				import IJ, ImageStack, ImagePlus
from ij.process 		import ImageProcessor,ShortProcessor, StackStatistics, ImageConverter, FloatProcessor, ImageConverter
from ij.measure 		import ResultsTable
from fiji.util.gui	 	import GenericDialogPlus
from java.awt  			import GridLayout, Font, Color
from ij 				import WindowManager as WM  
from inra.ijpb.measure 	import IntrinsicVolumes3D
from inra.ijpb.label 	import LabelImages
from inra.ijpb.plugins 	import AnalyzeRegions3D
from inra.ijpb.plugins 	import ParticleAnalysis3DPlugin, BoundingBox3DPlugin, ExtendBordersPlugin

def errorDialog(message):
	"""Outputs a given error for end users"""
	gd = GenericDialogPlus("Error")
	gd.addMessage(message)
	gd.showDialog()
	return


def imageSelectDialog():
	"""Select label map and training image"""
	imps = WM.getImageTitles()
	gd = GenericDialogPlus("Select image")
	gd.addChoice("Label map", imps, imps[0])
	gd.addChoice("ROI map", imps, imps[0])

	gd.showDialog()
	choices=gd.getChoices()
	labelMap=choices.get(0).getSelectedItem()
	roiMap=choices.get(1).getSelectedItem()
	
	if gd.wasCanceled():
		IJ.exit()
	return labelMap, roiMap

	

def createTrainingResultsTable(labelImp, roiImp):

	""" Exctracts all data required for each label in the image and writes to a results table to be used in the training - needs the label and ROI map to create the training data"""	
	height=labelImp.getHeight()
	width=labelImp.getWidth()

	frames=labelImp.getNFrames()
	depth=labelImp.getStackSize()/frames
	size = [width, height, depth]
	
	labelgtx=clij2.push(labelImp)
	roigtx=clij2.push(roiImp)

	#get label stats
	rtc = ResultsTable()
	clij2.statisticsOfLabelledPixels(roigtx, labelgtx, rtc)
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
	cropgtx=clij2.create([1,len(inputVector)],clij2.Float)
	clij2.crop(Graphgtx, cropgtx, 1,len(inputVector))
	i=0
	
	# use the maximumOfTouchingNeighbors to expand the network, then add on the orginal vector. Floods then maintains the gradient out
	while clij2.getMinimumOfAllPixels(cropgtx)==0:
		i=i+1
		clij2.maximumOfTouchingNeighbors(newGraphgtx, touchMatixgtx, gtx)
		clij2.addImages(gtx, Graphgtx, newGraphgtx)
		clij2.crop(newGraphgtx, cropgtx, 1,len(inputVector))
		if i==1000: # Just in case isolated things are passed
			print(clij2.getMinimumOfAllPixels(newGraphgtx))
			break
	clij2.pullToResultsTableColumn(newGraphgtx, rt, "placeholder", 0)
	inverseData=rt.getColumn("placeholder")

	#reverse direction of the map
	finalcolumn = map(lambda x: max(inverseData)-x,  inverseData)
	#print(finalcolumn)
	finalcolumn[0]=0.0
	#cleanup
	Graphgtx.close()
	newGraphgtx.close()
	gtx.close()
	GraphDistancesImp.close()
	return finalcolumn

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
	labelMapName, roiMapName = imageSelectDialog()
	IJ.log("Label map = " +str(labelMapName))
	IJ.log("ROI map = " +str(roiMapName))

	
	#get labels and Roi imageplus, push to gpu
	labelImp=WM.getImage(labelMapName)
	roiImp=WM.getImage(roiMapName)
	
	rtc2= createTrainingResultsTable(labelImp, roiImp)
	
	rtc2.show("Training data")
	
	clij2.clear()
	
	
	
	

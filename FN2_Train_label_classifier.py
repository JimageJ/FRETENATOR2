"""
******************************************************************************************
						Written by Jim Rowe (U of Sheffield)
								Started: 2026-02-19	
							 		@BotanicalJim
							james.rowe at sheffield.ac.uk

******************************************************************************************
"""
from ij 					import IJ
from ij.measure 			import ResultsTable
from fiji.util.gui 			import GenericDialogPlus
from java.awt  				import GridLayout, Font, Color
from ij 					import WindowManager as WM  
from datetime 				import datetime  
import os
import json


from jarray import array
from java.util import ArrayList, Random
from weka.core import SerializationHelper,  Attribute, Instances, DenseInstance
from weka.classifiers.trees import RandomForest



def errorDialog(message):
	"""Outputs a given error for end users"""
	gd = GenericDialogPlus("Error")
	gd.addMessage(message)
	gd.showDialog()
	return

def folderSelectDialog():
	"""Select training file or folder of training files"""
	imps = WM.getImageTitles()
	gd = GenericDialogPlus("Select training file or folder of training files")
	gd.addDirectoryOrFileField("Choose path", "")
	gd.addMessage('Choose parameters for random forest classifier')
	gd.addSlider("Number of trees", 50, 1000, 200, 10)
	gd.addSlider("Number of features", 1, 20, 5, 1)
	gd.addSlider("Depth of trees", 1, 20, 2, 1)
	gd.showDialog()	
	if gd.wasCanceled():
		IJ.exit()
	sliders=gd.getSliders()
	trees = sliders.get(0).getValue()*10
	features = sliders.get(1).getValue()
	treeDepth = sliders.get(2).getValue()
	
	
	print trees, features, treeDepth
	return gd.getNextString(),trees, features, treeDepth
	
def chooseColumns(columns, headingList):
	gd = GenericDialogPlus("Choose parameters for training")
	for i in range(len(headingList)):
		gd.addCheckbox(headingList[i],columns[i])

			
	gd.setLayout(GridLayout(0,3))	
	gd.showDialog()	
	checkBoxes=gd.getCheckboxes()
	choices=[]
	for i in range(len(checkBoxes)):
		boolchoice=gd.getNextBoolean()
		if boolchoice == True:
			choices.append(i)
		columns[i]=boolchoice
	if gd.wasCanceled():

		IJ.exit()
	return choices, columns

def filteredResultsTable(rtc, columnChoices):
	rtc2=ResultsTable()
	for j in range(rtc.size()):
		rtc2.addRow()
		for i in columnChoices:
			rtc2.addValue(rtc.getColumnHeading(i), rtc.getColumn(i)[j])
	return rtc2


def concatResultsTable(rt1, rtc):
	
	rtcheadingList=rtc.getColumnHeadings().split()
	
	#morphResults.show("huh")
	rt1headingsList = rt1.getColumnHeadings().split()
	
	#combine both data tables and display the training data file

	for j in range(rtc.size()):
		rt1.addRow()
		for i in range(len(rtcheadingList)):
			rt1.addValue(rtcheadingList[i], rtc.getColumn(i)[j])
			#print(j)
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

	print len(attributes)
	print n_attributes
	input_data = Instances("training", attributes, len(samples))
	input_data.setClassIndex(len(attributes) -1) # the last one is the class
	for vector in samples:
		input_data.add(DenseInstance(1.0, vector))
	return input_data, attributes


try: 
	from net.haesleinhuepf.clijx import CLIJx
	#from net.haesleinhuepf.clij2 import CLIJx

except:
	errorDialog("""This plugin requires clij2 to function. 
	
	To install please follow these instructions: 
	
	1. Click Help>Update> Manage update sites
	2. Make sure the "clij" and "clij2" update sites are selected.
	3. Click Close> Apply changes.
	4. Close and reopen ImageJ""")

clij2 = CLIJx.getInstance()
# *****************************body of code starts****************************************
	
if __name__ == "__main__":
	
	clij2.clear()
	
	filePath, trees, features, treeDepth =folderSelectDialog()
	rt=ResultsTable()
	
	if os.path.isfile(filePath):
		rt1=ResultsTable.open(filePath)
		
	else:
		fileList=os.listdir(filePath)
		for i in fileList:
			if i[-4:]==".csv":
				rt1=ResultsTable.open(filePath+ "/" +i)
				concatResultsTable(rt, rt1)
	
	rtheadingsList = rt.getColumnHeadings().split()
	
	columns = [False, False, False, False, False, False, False, True, True, True, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, True, True, True, False, False, False, False, True, True, True, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
	#columns = [1]*len(rtheadingsList)	
	columnChoices, columns= chooseColumns(columns, rtheadingsList)
	print columns
	rt2= filteredResultsTable(rt, columnChoices)
	#rt2.show('filtered')
	training_data, attributes= convertTableToInstances(rt2)
	date= datetime.now().strftime("%Y-%m-%d-%H.%M")
	#clij2.trainWekaFromTable(rt2, 'LABEL_ID', filePath + "/" + date + " classifier.model", 500, 10,10)

	
	classifier = RandomForest() 
	classifier.setNumIterations(trees)
	classifier.setNumFeatures(features)
	classifier.setMaxDepth(treeDepth)
	classifier.buildClassifier(training_data)
	SerializationHelper.write(filePath + "/" + date + " classifier.model", classifier)  
	with open(filePath+"/"+date+' classifier_fileheaders.json', 'w') as f:
		json.dump(columns, f)
	
		
	
	

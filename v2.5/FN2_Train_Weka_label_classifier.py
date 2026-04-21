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
import array  
from datetime 				import datetime  
import os
import json

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
	gd.showDialog()	
	if gd.wasCanceled():
		IJ.exit()
	return gd.getNextString()
	
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
			#print(j)
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
	
	filePath=folderSelectDialog()
	rt=ResultsTable()
	
	if os.path.isfile(filePath):
		rt1=ResultsTable.open(filePath)
		
	else:
		fileList=os.listdir(filePath)
		for i in fileList:
			if i[-4:]==".csv":
				print i
				rt1=ResultsTable.open(filePath+ "/" +i)
				
				concatResultsTable(rt, rt1)
	
	#rt.show("data")
	rtheadingsList = rt.getColumnHeadings().split()
	
	#columns = [True, False, False, False, False, False, False, True, True, True, False, False, False, False, False, True, False, False, False, True, True, True, False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
	columns = [0]*len(rtheadingsList)	
	columnChoices, columns= chooseColumns(columns, rtheadingsList)
	
	rt2= filteredResultsTable(rt, columnChoices)
	rt2.show('filtered')
	
	date= datetime.now().strftime("%Y-%m-%d-%H.%M")
	clij2.trainWekaFromTable(rt2, 'LABEL_ID', filePath + "/" + date + " classifier.model", 500, 10,10)

	with open(filePath+"/"+date+' classifier_fileheaders.json', 'w') as f:
		#	f.write(str(columns))
		json.dump(columns, f)
		
	
	

# FRETENATOR2- Comprehensive segmenation and ratiometric analysis

Latest version of FRETENATOR segmentation and ratiometric analysis suite. This is currently a prerelease version.

New FRETENATOR2 implemented features:

* Improved user interface, Background subtraction (Global mean or Local label based), Pixel by pixel processing, Setting saving/reloading, Headless mode for batch, 2D image processing

Planned features
* 32 bit emission ratio image outputs (no 1000X multiplication)

Possible planned features:

* Quick segmentation settings button, Cell type classification, Alternative segmentation methods
  
### **Installation**

Install CLIJ and CLIJ2 by activating their update sites, then copy the **'FRETENATOR2_'** folder into the Fiji/plugins folder and restart Fiji.

## **FRETENATOR2_Segment_and_ratio**


![nlsABACUS2 confocal image](https://github.com/JimageJ/FRETENATOR2/blob/main/imagefiles/image20.gif)
![nlsABACUS2 segmentation performed with FRETENATOR](https://github.com/JimageJ/FRETENATOR2/blob/main/imagefiles/image22.gif)
![nlsABACUS2 emission ratio, with calculations performed on a per object basis](https://github.com/JimageJ/FRETENATOR2/blob/main/imagefiles/image21.gif)


# **Usage**:

*FRETENATOR2 Segment and ratio* is a powerful plugin to quickly perform ratiometric analysis of 2D, 3D or 4D microscopy images,  with an new user interface and a live updating preview. The plugin performs full 3D segmentation of images, which means you don't analyse background, and does all the analysis, ready for you to plot and interpret. The algorithm can be used to analyse punctate sensors (e.g. nuclear localised) on a per object basis, or diffuse sensors (e.g. cytoplasmic) on a pixel by pixel basis, with guideline settings below. Saturated pixels are automatically removed. Settings can be saved and used for headless processing, or even batch (alpha).

• Results Table:    ◦ Includes the ratiometric calculation (emission ratio) your channel quantifications, and x, y, z positions. This can be saved as a .csv and then analysed in python, R or excel.

• Threshold map:    ◦ An image of the initial thresholding use for analysis

• Label map:    ◦ An image in which every nucleus is given a value that corresponds to the “label” in the results table.

• Emission ratio map:    ◦ An image in which every nucleus is given the value of it’s emission ratio X 1000

• Max Z projected emission ratio map:    ◦ A maximum Z projection of the emission ratio map

• Nearest point emission ratio map:    ◦ A nearest point projection of the emission ratio map, with outlines added between the nuclei NB: the scale of this image is different to the original image and other images, allowing thin outlines to be drawn.

• Log:     ◦ Details of the image file and exact analysis settings used to keep with your metadata. Savable as a .txt file


# **FRETENATOR2 SEGMENT AND RATIO TUTORIAL** 

https://www.youtube.com/watch?v=OdPR_2kKuzg

# **Setting LUTs and making a colourbar**

https://www.youtube.com/watch?v=rTH1vWirORI



# **Settings for localised sensors, e.g. Nuclei**


Switch on 'Difference of Gaussian instead of Gaussian'

Set the small DoG filter between 0.5-1.2, and the large DoG filter about half the diameter of a typical nucleus in pixels

Autosegmentation method : Otsu

Switch on 'Watershed Object splitting' if your nuclei are close together

Switch OFF 'Use pixel by pixel analysis' to allow quantification to be performed on a per object basis

Max intensity: 4094 for 12 bit images, 65534 for 16 bit images



# **Settings for diffuse sensors (e.g. cytoplasmic)**


Switch OFF 'Difference of Gaussian instead of Gaussian'

Set the small DoG filter between 0.5-1.2 the large DoG filter isn't used

Autosegmentation method : Otsu

Switch OFF 'Watershed Object splitting'

Switch ON 'Use pixel by pixel analysis' to allow quantification to be performed on a per object basis

Max intensity: 4094 for 12 bit images, 65534 for 16 bit images



![cytosolic ABACUS1 confocal image](https://github.com/JimageJ/FRETENATOR2/blob/main/imagefiles/PixelXPixel2.png)
![cytosolic ABACUS1 analysed pixel by pixel](https://github.com/JimageJ/FRETENATOR2/blob/main/imagefiles/pixelXpixel1.png)



### Technical implementation (jargon)

The segmentation tool works by a DoG or Gaussian filter, then Otsu to generate a binary map. An optional watershed can then be used to split objects, but a 3D watershed it a little too severe and causes the loss of many nuclei and many shrink down much smaller than their original size. By comparing my watershed to non watersheded binary maps I can create a map of the 'lost nuclei' to add them back in later. A connected components analysis is used to generate a label map of the watersheded nuclei, and then dilated the labelmap on zero pixels only to fill all the space. I then multiply this by the orginal threshold image to get a a good segmentation with good enough split objects. But this will give incorrect labelling to the 'lost nuclei' present in the image. To correct this, I run a connected components on the 'lost nuclei' map, to generate  labels, and add on the max value of the OTHER label map. Then I use maximumImage to superimpose these labels on the other label map to get my FINAL label map.

The software will then use the segmentation to quantify statistics (postion, intesnity etc) for each nucleus for the chosen channel.
Built upon the nuclear segmentation tool. Gives a dialog with segmentation settings, which can be adjusted in real time with a live labelmap max projection preview of frame 1. Pleasse note that the DoG filter and tophat background subtraction are only used to segment the image and are not applied to the channels to be quantified.

The chosen settings will then be applied to the time series and the data for emission ratio calculation etc are output to a results table. This is useful for ratiometric biosensors. Voxels saturated in the **Donor** or **Emission (FRET)** channels are excluded from analysis.

The "nearest point Z projection" option has outline drawing between segmented objects. This will make pretty Z projections where the different objects are discernable and overlayed properly.

There are two background subtraction methods. Global mean subtraction, subtracts the average intensity of the are excluded from segmentation in each channel from each pixel before performing calculation - this is good for the global background signal that is present in many camera/detector types. Local label based subtraction will process each ROI object individually, subtracting the average intensity of nearby pixels in the excluded area surrounding it, which is good for global background as well as local background such as light scattering/autofluorescence.

## **FRETENATOR2_SaR_Headless**

Uses the last saved settings of FRETENATOR2_Segment_and_ratio, and performs analysis without opening a dialog box (faster).


## **FRETENATOR2_SaR_Batch (alpha)**

*Currently only reliable when run from the script editor* Uses the last saved settings of FRETENATOR2_Segment_and_ratio, and performs analysis on all images in a user defined folder, then exports the analysis into another user defined folder.


## **FRETENATOR_Labeller (Beta)**

### Implementation and usage

A follow on tool for after segmentations where users can categorise the ROI in their segmented images. As a work in progress, it currently works on single timepoint 3D label images, allowing users to visually assign labels to one of 10 categories. Results are either output to an existing results table or can be used to measure a chosen image. ***Alpha functionality:*** In the latest version, time course analysis can be performed, but usage asumes the same label usage through time (making it compatable with Trackmate exported files - see below).

**Usage:**
FRETENATOR ROI Labeller tutorial
https://www.youtube.com/watch?v=EKXR4z5g8Pg

## **FRETENATOR_Trackmate_Bridge (Alpha)**

A simple plugin to allow **Trackmate 7** analysed label images (Analyse the FRETENATOR label map for tracking then export the tracked label map as dots) to be combined with **FRETENATOR_Segment_and_ratio** output. This adds TrackIDs to the results table and creats a new TrackID labelmap that can be analysed with the ROI manager.

![Stomata](https://github.com/JimageJ/FRETENATOR2/blob/main/imagefiles/image29.gif)
![Stomata ROI labeled image after tracking with Trackmate](https://github.com/JimageJ/ImageJ-Tools/blob/master/images/labeled%20stomata.gif)

## **Troubleshooting**

All these plugins use CLIJ/CLIJ2 to process images on the graphics card. This means image processing is lightning fast, but also means there are sometimes errors/crashes.

The majority of these crashes are due to one of two reasons:
**i.** the image stack being too large to process on the graphics card this can be solved by using a computer with more video memory, or scaling/cropping the images to be smaller. Normally 4-5x the image size is required in video memory. Running Plugins>ImageJ on GPU (CLIJ2)>Macro tools>CLIJ2 Clinfo will allow you to select GPU and provide info on the hardware’s maximum image size.

or **ii.** out of date graphics card drivers. This often presents with black/blank images. This can often be solved by downloading the latest drivers from the manufacturer website (usually AMD, Nvidia or intel). 





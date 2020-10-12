# CanopyGapAnalyzer

Segmentation and analysis of hemispherical images to estimate leaf area index (LAI) and further parameters

![figure](doc/TSsmall.jpg)

These tools are designed to calculate Leaf Area Index (LAI) and further canopy parameters, such as transmission and gap fraction, for batches of hemispherical images.
The first step is a segmentation of the image into plant/sky pixels. The segmentation method used here is a novel approach based on local contrast enhancement and allows also to process images that were taken in not ideal conditions. 

![segmentation](doc/segmentation.png)

The image is then split into a number of concentrical circles and angular segment, and the transmission for each segment is calculated. 

Different functions to calculate LAI were implemented, according to following publications:
* Norman, J.M., Campbell, G.S., 1989. Canopy structure. In: Pearcy, R.W., Ehleringer, J.R., Mooney, H.A., Rundel, P.W. (Eds.), Plant Physiological Ecology: Field Methods and Instrumentation. Chapman and Hall, London, New York, pp. 301–325.
* Miller, J.B., 1967. A Formula for Average Foliage Density. _Australian Journal of Botany_, 15(1), pp. 141-&. 
* Lang (1987) Simplified estimate of leaf area index from transmittance of the sun's beam. _Agricultural and Forest Meteorology, 41 (1987) 17~186 
* LI-COR, 1992. LAI-2000 Plant Canopy Analyser. Instruction manual. LICOR, Lincoln, NE, USA. 

In addition, the code also includes some variations of these methods. 

## Tools
The tools provided with this script are:
* ImageSetup.py: a GUI tool in order to set mark the rotation (set North) and mask certain areas of the image to be ignored (sun) or analyzed separately (requires [https://glade.gnome.org/] (glade) ).
* NorthCorrected.py: Rotate Images so that North is on top. This script uses the parameters in the *.par file (as created my ImageSetup.py) to determine the rotation angle.
* Overview.py: Stack images together to create a nice overview (Servers a template only, needs to be edited according to the number of images)


## Installation and Usage

Just copy the files into a filder of your choice. Run the script by
```    
CGA.py [imagepath] [outpath]
```    
e.g.
```    
./cga/CGA.py ../tests ../out
```    
the output directory will be created if not yet existant.
    
## Parameter File
For each Image, a parameter file is created. The file contains 2 lines, a header and a data line (columns separated by semicolons):
```
SITE;OBS;LAT;LON;ALT;TIME;CENTER;RADIUS;NORTH;WOOD
F1_001;O1;47.70488;7.470766;244;24.03.2011 10:13:47;[1000, 800];750;280.400983435;Test1.jpg
```

The Fields are defined as follows:
* SITE: Site identifier
* OBS: Observation identifier
* LAT: Geographical latitude
* LON: Geographical longitude
* ALT: Elevation
* TIME: Date and time when the image was taken
* CENTER: [x,y]  coordinates of the center pixel
* RADIUS: Radius of the Image
* NORTH: Rotation angle indicating the direction to North
* WOOD: the path to the reference image that does not have leaves (to accurately estimate LAI)

## Note
This code was first written 2011, I'm currently testing if it still works as intended. There are still many hard-coded parameters that can be should be made accessible as command line arguments
Update Oct. 2020: The main code CGA.py is now Python3 compatible. Tools still need to be tested


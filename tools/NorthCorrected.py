import os,sys
import Image
import numpy as np

def listallfiles(basePath):
	basePath=basePath.replace("\\","/")
	if os.path.exists(basePath)==False:
		print "Path does not exits"
		return
	filelist=[]
	for root, dirs, files in os.walk(basePath):
		for f in files:
			f=f.lower()
			if f.endswith('.jpg') or f.endswith('.jpeg'):
				file=os.path.join(root,f)
				file=file.strip()
				file=file.replace("\\","/")
				filelist.append(file)
	return filelist

def getNorth(imagename):
	parfile=imagename.split(".")[0]+".par"
	if os.path.exists(parfile)==False:
		print "no metadata: ("+ parfile.split("/")[-1]+"): setting north to 0.0"
		north=0.0
	else:
		print "reading metadata from "+ parfile.split("/")[-1]
		pfile= open(parfile,'r')
		parline=pfile.readlines()[0]
		pfile.close()
		parline=parline.strip()
		parline=parline.split(';')
		north=float(parline[3])
	return north

def RotImages(fl,OUTpath):
	for f in fl:
		print f
		fn= os.path.split(f)[1]
		north=getNorth(f)
		img = Image.open(f)
		img.load()
		img=img.crop((250,50,1750,1550))
		img=img.rotate(north)
		if os.path.exists(OUTpath+fn[:6].capitalize()+"/")==False:
			os.mkdir(OUTpath+fn[:6].capitalize()+"/")
		img.save(OUTpath+fn[:6].capitalize()+"/"+fn.capitalize())
		del img



fl=listallfiles("C:/PHD/GroundObservations/Data/TimeSeries")
BINpath="C:/PHD/GroundObservations/Results/LAI/BINS/"
OUTpath="C:/PHD/GroundObservations/Results/ROTATED/"

if os.path.exists(OUTpath)==False:
	print "creating output directory"
	os.mkdir(OUTpath)

RotImages(fl,OUTpath)

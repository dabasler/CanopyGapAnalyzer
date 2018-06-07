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

def makeF1Overview(fl,res,OUTpath,BIN,BINPath):
	for i in range(1,9):
		BigImg=Image.new("RGB", (11*res,10*res))
		obs="o"+str(i)
		for f in fl:
			fn= os.path.split(f)[1]
			if fn[:2]=="f1" and fn[7:9]==obs:
				id=int(fn[3:6])
				y=(id-1)/11
				if y%2==0:
					x=11-id%11
					if x==11: x=0
				else:
					x=id%11-1
					if x==-1: x= 10
				north=getNorth(f)
				if BIN==True:
					f=BINpath+fn[:-4]+"_bin.bmp"
				img = Image.open(f)
				img.load()
				if BIN==False:
					img=img.crop((250,50,1750,1550))
				img=img.rotate(north)
				img=img.resize((res,res),Image.ANTIALIAS)
				BigImg.paste(img,(x*res,y*res))
				del img
		if BIN==True:
			BigImg.save(OUTpath+"BIN_F1"+obs+".bmp")
		else:
			BigImg.save(OUTpath+"F1"+obs+".bmp")



def makeF2Overview(fl,res,OUTpath,BIN,BINPath):
	for i in range(2,9):
		BigImg=Image.new("RGB", (6*res,6*res))
		obs="o"+str(i)
		for f in fl:
			fn= os.path.split(f)[1]
			id=int(fn[3:6])
			if (fn[:2]=="f2" and fn[7:9]==obs) and not id==37:
				y=(id-1)/6
				if y%2==0:
					x=6-id%6
					if x==6: x=0
				else:
					x=id%6-1
					if x==-1: x= 5
				north=getNorth(f)
				if BIN==True:
					f=BINpath+fn[:-4]+"_bin.bmp"
				img = Image.open(f)
				img.load()
				if BIN==False:
					img=img.crop((250,50,1750,1550))
				img=img.rotate(north)
				img=img.resize((res,res),Image.ANTIALIAS)
				BigImg.paste(img,(x*res,y*res))
				del img
		if BIN==True:
			BigImg.save(OUTpath+"BIN_F2"+obs+".bmp")
		else:
			BigImg.save(OUTpath+"F2"+obs+".bmp")



fl=listallfiles("C:/PHD/GroundObservations/Data/TimeSeries")
BINpath="C:/PHD/GroundObservations/Results/LAI/BINS/"
OUTpath="C:/PHD/GroundObservations/Results/Overview/"
res=110
BIN=True

if os.path.exists(OUTpath)==False:
	print "creating output directory"
	os.mkdir(OUTpath)

makeF1Overview(fl,res,OUTpath,True,BINpath)
makeF1Overview(fl,res,OUTpath,False,BINpath)

makeF2Overview(fl,res,OUTpath,True,BINpath)
makeF2Overview(fl,res,OUTpath,False,BINpath)

#!/usr/bin/env python

###################
# Image Segmentation and coding
###################
###########################################################################################
# IMAGE IMPORT AND BASIC PROCESSING
# INCL. IMAGE TO BINARY MASK CONVERSION

def getMask(imagename):
	print ('import mask')
	img = Image.open(imagename)
	img.load()
	img=img.convert('L') # Prevents crash (converting type '1' img to array doesn't work...)
	imgArray = np.asarray(img)
	imgArray=imgArray/255
	return imgArray

def getRGB(imagename,imgcenter,imgradius,square=True):
	img = Image.open(imagename)
	img.load()
	imgR,imgG,imgB = img.split()
	R = np.asarray(imgR)
	G = np.asarray(imgG)
	B = np.asarray(imgB)
	if square==True:
		R=squareArray(R,imgcenter,imgradius)
		G=squareArray(G,imgcenter,imgradius)
		B=squareArray(B,imgcenter,imgradius)
	return R,G,B

def squareArray(array,center,radius):
	arrshape=array.shape
	new_array=np.zeros((2*radius)*(2*radius),dtype=np.uint8).reshape((2*radius),(2*radius))
	left=int(center[0]-radius)
	right=int(center[0]+radius)
	top=int(center[1]-radius)
	bottom=int(center[1]+radius)
	ntop=0
	nleft=0
	nright=2*radius
	nbottom=2*radius
	if top<0:
		ntop=abs(top)
		top=0
	if left<0:
		nleft=abs(left)
		left=0
	if bottom>arrshape[0]:
		nbottom=nbottom-(bottom-arrshape[0])
		bottom=arrshape[0]
	if right>arrshape[1]:
		nright=nright-(right-arrshape[1])
		right=arrshape[1]
	new_array[ntop:nbottom,nleft:nright]=array[top:bottom,left:right]
	return new_array

def getSkyMask(name,gamma,max_fov,set_square,center,inv_pix): #Oct 2011 Added inv_pix
	global BasicMaps,USE_EXISTING_BINARYMASKS
	sourceImage=getRGB(name,center,max_fov,square=set_square)
	if USE_EXISTING_BINARYMASKS==True:
		BINname=os.path.join(BINpath,name.split('/')[-1].split('.')[0]+"_bin.bmp")
		if os.path.exists(BINname)==True:
			skymask=getMask(BINname)
		else:
			skymask = ImageFiltering(name,sourceImage,gamma)	
	else:
		skymask = ImageFiltering(name,sourceImage,gamma)
	skymask[(BasicMaps[2]<=(max_fov*max_fov))==0]=2 # Set pixels ouside max_fov to CODE 2 (ignore)
	if not len(inv_pix)==0: # Set NON Vailid (Sunburn) pixels to CODE 3 (ignore)
		inv_pix=np.transpose(np.array(inv_pix))
		inv_pix[0]=inv_pix[0]+max_fov#center[0]
		inv_pix[1]=inv_pix[1]+max_fov#+center[1]
		inv_pix=inv_pix[:,~(inv_pix[0]>skymask.shape[0])&~(inv_pix[1]>skymask.shape[1])&~(inv_pix[0]<0)&~(inv_pix[1]<0)]
		if inv_pix.shape[1]==0:
			return skymask
		else:
			print ("masking "+ str(len(inv_pix[0]))+ " invalid pixels")
		inv_pix=[list(inv_pix[1]),list(inv_pix[0])] # arrays are y,x
		skymask[inv_pix]=3
	return skymask

def LCenhance(imgarray,sigma,k):
	smooth=np.zeros(imgarray.shape[0]*imgarray.shape[1],dtype=np.int16).reshape(imgarray.shape)
	smooth=smooth+imgarray
	smooth=gaussian_filter(smooth,sigma)
	smooth=imgarray-smooth
	overlay=imgarray+k*smooth
	overlay[overlay>255]=255
	overlay[overlay<0]=0
	overlay=np.array(overlay,dtype=np.uint8)	
	return overlay

def SobelEdges(arr):
	arr=np.array(arr,dtype=np.int16)
	arrmx=arr-np.column_stack([arr[:,1:],arr[:,-1]])
	arrpx=arr-np.column_stack([arr[:,0],arr[:,0:(arr.shape[1]-1)]])
	arrmy=arr-np.vstack([arr[1:,:],arr[-1,:]])
	arrpy=arr-np.vstack([arr[0,:],arr[0:(arr.shape[0]-1),:]])
	arrpxpy=np.vstack([arrpx[0,:],arrpx[0:(arr.shape[0]-1),:]])
	arrpxmy=np.vstack([arrpx[1:,:],arrpx[-1,:]])
	arrmxpy=np.vstack([arrmx[0,:],arrmx[0:(arr.shape[0]-1),:]])
	arrmxmy=np.vstack([arrmx[1:,:],arrmx[-1,:]])
	SobelX=2.0*arrmx-2*arrpx+arrmxpy+arrmxmy-arrpxpy-arrpxmy
	SobelY=2.0*arrmy-2*arrpy+arrmxmy+arrpxmy+arrmxpy+arrpxpy
	sqsum=(SobelX*SobelX)+(SobelY*SobelY)
	arr=np.sqrt(sqsum) #arr=threshold(arr,thrsh)
	return arr

def ImageFiltering(name,ImageArray,gamma):
	DEBUG=False
	print ('filtering '+ name)
	R,G,B=ImageArray[0],ImageArray[1],ImageArray[2]
	if not gamma==1.0: 	# gamma expansion
		R=np.array(np.power((R/255.0),gamma)*255,dtype=np.uint8) 
		G=np.array(np.power((G/255.0),gamma)*255,dtype=np.uint8)
		B=np.array(np.power((B/255.0),gamma)*255,dtype=np.uint8)	
	flt_smooth=gaussian_filter(B,0.5) 	# remove Jpeg artefacts for edge detection
	flt_edge=SobelEdges(flt_smooth)
	flt_thres=110+50*((flt_edge/255.0)-0.5) 		### CRITICAL POINT
	flt_enhance=LCenhance(B,30,5)
	flt_enhance[flt_enhance<=flt_thres]=0 			#Threshold 
	flt_enhance[flt_enhance>flt_thres]=255	
	flt_enhance[G>1.1*B]=0
	flt_enhance[R>1.1*B]=0
	if DEBUG==True:
		Image.fromarray(B).show()
		Image.fromarray(flt_enhance).show()
		Image.fromarray(flt_edge).show()
		Image.fromarray(flt_thres).show()
	img = Image.fromarray(flt_enhance).convert('1')
	img.save(os.path.join(BINpath,name.split("/")[-1].split('.')[0]+"_bin.bmp"))
	flt_enhance[flt_enhance>0]=1
	flt_enhance=np.array(flt_enhance,dtype=np.uint8)
	del img,flt_smooth,flt_thres,flt_edge,R,G,B
	return flt_enhance

###########################################################################################
# BASIC LINE DRAWING FUNCTIONS

def line(px0, py0, px1, py1,setPixel,col_val):
	ym=setPixel.shape[0]-1
	xm=setPixel.shape[1]-1
	if px0<0: px0=0
	if px1<0: px1=0
	if py0<0: py0=0
	if py1<0: py1=0
	if px0>xm: px0=xm
	if px1>xm: px1=xm
	if py0>ym: py0=ym
	if py1>ym: py1=ym
	dx = abs(px1-px0)
	dy = abs(py1-py0)
	if px0 < px1:
		sx = 1
	else:
		sx= -1
	if py0 < py1: 
		sy = 1
	else:
		sy = -1
	err = dx-dy
	while(1):
		setPixel[py0,px0]=col_val
		if px0 == px1 and py0 == py1:
			break
		e2 = 2*err
		if e2 > -dy:
			err = err - dy
			px0 = px0 + sx
		if e2 <  dx:
			err = err + dx
			py0 = py0 + sy
	return setPixel

def rasterCircle(x0,y0,radius,setPixel,col_val):
	#http://en.wikipedia.org/wiki/Midpoint_circle_algorithm
	xm=setPixel.shape[0]-1
	ym=setPixel.shape[1]-1
	f = 1 - radius
	ddF_x = 1
	ddF_y = -2 * radius
	x = 0
	y = radius
	y1= int(y0 + radius)
	y2= int(y0 - radius)
	x1= int(x0 + radius)
	x2= int(x0 - radius)
	if y2<0: y2=0
	if y1>ym: y1=ym
	if x1<0: x1=0
	if x1>xm: x1=xm
	setPixel[x0, y1]=col_val
	setPixel[x0, y2]=col_val
	setPixel[x1, y0]=col_val
	setPixel[x2, y0]=col_val
	while(x < y):
		if(f >= 0):
			y=y-1
			ddF_y =ddF_y + 2
			f= f+ddF_y
		x=x+1
		ddF_x = ddF_x + 2
		f = f + ddF_x
		y1=y0+y
		y2=y0-y
		y3=y0+x
		y4=y0-x
		x1=x0+x
		x2=x0-x
		x3=x0+y
		x4=x0-y
		if y1<0: y1=0
		if y2<0: y2=0
		if y3<0: y3=0
		if y4<0: y4=0
		if y1>ym: y1=ym
		if y2>ym: y2=ym
		if y3>ym: y3=ym
		if y4>ym: y4=ym
		if x1<0: x1=0
		if x2<0: x2=0
		if x3<0: x3=0
		if x4<0: x4=0
		if x1>xm: x1=xm
		if x2>xm: x2=xm
		if x3>xm: x3=xm
		if x4>xm: x4=xm
		x1,x2,x3,x4 = int(x1),int(x2),int(x3),int(x4)
		y1,y2,y3,y4 = int(y1),int(y2),int(y3),int(y4)
		setPixel[x1, y1]=col_val
		setPixel[x2, y1]=col_val
		setPixel[x1, y2]=col_val
		setPixel[x2, y2]=col_val
		setPixel[x3, y3]=col_val
		setPixel[x4, y3]=col_val
		setPixel[x3, y4]=col_val
		setPixel[x4, y4]=col_val
	return setPixel

def getCirclePix(x0,y0,radius):
	r2=radius*radius
	shape=(2*radius,2*radius)
	x=np.array([range(shape[1])] * shape[0]).reshape(shape) -radius					# Pixel X Pos
	y=np.array([range(shape[0])] * shape[1]).reshape(shape[1],shape[0]) -radius		# Pixel Y Pos
	y=np.flipud(np.rot90(y))
	c=x*x+y*y							# circle Definition x^2+y^2
	cp=zip(*[x[c<=r2]+x0,y[c<=r2]+y0])
	return cp

def draw_slope(r,slope,aspect,x0,y0,setPixel,col_value):
	#ellipse
	n=30
	aspect=aspect*(np.pi/180)
	slope=slope*(np.pi/180)
	a=r
	b=r*np.cos(slope)
	cosphi = np.cos(aspect)
	sinphi = np.sin(aspect)
	A = a*cosphi
	B = b*sinphi
	C = a*sinphi
	D = b*cosphi
	x1 = A + x0
	y1 = C + y0
	theta = 0
	incr = np.pi/n # only one half use 2*pi for full ellipse
	for j in range(n):
		theta = theta+ incr
		costheta = np.cos(theta)
		sintheta = np.sin(theta)
		x2 = A*costheta - B*sintheta + x0
		y2 = C*costheta + D*sintheta + y0
		setPixel=line(int(x1),int(y1),int(x2),int(y2),setPixel,col_value)
		x1 = x2
		y1 = y2
	return(setPixel)

###########################################################################################
# ANALYSIS GRID DRAWING FUNCTIONS

def drawGrid(shape,center,nrings,nsectors,north,fov,max_fov,rings,slope_par):
	deg_per_ring=fov/(nrings*1.0)
	x0,y0=center
	rmax=LensCorr(max_fov,fov)
	alpha=360/(nsectors*1.0)
	grid=np.zeros(shape[1]*shape[0],dtype=np.uint8).reshape(shape)			#LineLayer
	# LENS Limit
	grid=rasterCircle(y0,x0,max_fov,grid,1)
	# Rings
	k=0
	for i in range(nrings):
		grid=rasterCircle(y0,x0,LensCorr(max_fov,rings[k]),grid,2)
		grid=rasterCircle(y0,x0,LensCorr(max_fov,rings[k+1]),grid,6)
		k=k+2
	#Data Limit
	grid=rasterCircle(y0,x0,rmax,grid,4) 
	# Sectors
	if nsectors>1:
		for i in range(nsectors):
			deg=north+i*alpha
			y1=int(y0+rmax*np.sin(np.pi*(deg-90)/180.0))
			x1=int(x0+rmax*np.cos(np.pi*(deg-90)/180.0))
			grid=line(x0,y0,x1,y1,grid,2)
	# NORTH Tag
	north_r=north*(np.pi/180)
	y1=int(y0-0.95*max_fov*np.cos(north_r))
	x1=int(x0+0.95*max_fov*np.sin(north_r))
	y2=int(y0-1.05*max_fov*np.cos(north_r))
	x2=int(x0+1.05*max_fov*np.sin(north_r))
	grid=line(x1,y1,x2,y2,grid,1)
	# Center
	y1=int(y0-(-0.05)*max_fov*np.cos(north_r))
	x1=int(x0+(-0.05)*max_fov*np.sin(north_r))
	y2=int(y0-0.05*max_fov*np.cos(north_r))
	x2=int(x0+0.05*max_fov*np.sin(north_r))
	grid=line(x1,y1,x2,y2,grid,7)
	y1=int(y0-0.05*max_fov*np.sin(north_r))# turn aspect
	x1=int(x0-0.05*max_fov*np.cos(north_r))
	y2=int(y0+0.05*max_fov*np.sin(north_r))# turn aspect
	x2=int(x0+0.05*max_fov*np.cos(north_r))
	grid=line(x1,y1,x2,y2,grid,7)
	# Slopes
	slope,aspect=slope_par
	if slope >0:
		grid=draw_slope(max_fov,slope,aspect,x0,y0,grid,5)
		# aspect tag
		aspect_r=aspect*(np.pi/180)
		y1=int(y0-0.95*max_fov*np.cos(aspect_r))
		x1=int(x0+0.95*max_fov*np.sin(aspect_r))
		y2=int(y0-1.05*max_fov*np.cos(aspect_r))
		x2=int(x0+1.05*max_fov*np.sin(aspect_r))
		grid=line(x1,y1,x2,y2,grid,5)
		#Normal Center
		y1=int(y0-max_fov*np.sin(slope_r)*np.cos(aspect_r)+0.05*max_fov*np.cos(aspect_r))
		x1=int(x0+max_fov*np.sin(slope_r)*np.sin(aspect_r)-0.05*max_fov*np.sin(aspect_r))
		y2=int(y0-max_fov*np.sin(slope_r)*np.cos(aspect_r)-0.05*max_fov*np.cos(aspect_r))
		x2=int(x0+max_fov*np.sin(slope_r)*np.sin(aspect_r)+0.05*max_fov*np.sin(aspect_r))
		grid=line(x1,y1,x2,y2,grid,5)
		x1=int(x0+(np.sin(aspect_r)*max_fov*np.sin(slope_r)-np.cos(aspect_r)*0.05*max_fov))
		y1=int(y0-(np.cos(aspect_r)*max_fov*np.sin(slope_r)+np.sin(aspect_r)*0.05*max_fov))
		x2=int(x0+(np.sin(aspect_r)*max_fov*np.sin(slope_r)+np.cos(aspect_r)*0.05*max_fov))
		y2=int(y0-(np.cos(aspect_r)*max_fov*np.sin(slope_r)-np.sin(aspect_r)*0.05*max_fov))
		grid=line(x1,y1,x2,y2,grid,5)
	if ViewCap[0]>0:
		VC1=north+ViewCap[1]-ViewCap[0]/2.0
		VC2=north+ViewCap[1]+ViewCap[0]/2.0
		VC1=VC1*(np.pi/180)
		VC2=VC2*(np.pi/180)
		y1=int(y0-rmax*np.cos(VC1))
		x1=int(x0+rmax*np.sin(VC1))
		grid=line(x0,y0,x1,y1,grid,4)
		y1=int(y0-rmax*np.cos(VC2))
		x1=int(x0+rmax*np.sin(VC2))
		grid=line(x0,y0,x1,y1,grid,4)
	# Slopes line
	return grid

def drawGridOutupt(shape,center,nrings,nsectors,north,fov,max_fov,rings,ViewCap,ViewCapMask,slope_par,SlopeMask):
	global BasicMaps
	deg_per_ring=fov/(nrings*1.0)
	north_r=north*(np.pi/180)
	x0,y0=center
	rmax=LensCorr(max_fov,fov)
	alpha=360/(nsectors*1.0)
	grid=np.zeros(shape[1]*shape[0],dtype=np.uint8).reshape(shape)			#LineLayer
	# Rings
	rings=LensCorr(max_fov,np.array(rings,dtype=np.float32))
	k=1
	for i in range(1,nrings):
		if not rings[k+1]==rings[k]:
			c1=BasicMaps[2]>(rings[k]*rings[k])
			c2=BasicMaps[2]<=(rings[k+1]*rings[k+1])
			grid[c1&c2]=1
		k=k+2
		
	if fov<90:
			c1=BasicMaps[2]>(rings[-1]*rings[-1])
			c2=BasicMaps[2]<(max_fov*max_fov)
			grid[c1&c2]=1
	k=0
	for i in range(nrings):
		grid=rasterCircle(y0,x0,rings[k],grid,2)
		grid=rasterCircle(y0,x0,rings[k+1],grid,6)
		k=k+2
	#Data Limit
	grid=rasterCircle(y0,x0,rmax,grid,4) 
	# Sectors
	grid[BasicMaps[2]>(max_fov*max_fov)]=0
	if nsectors>1:
		for i in range(nsectors):
			deg=north+i*alpha
			y1=int(y0+rmax*np.sin(np.pi*(deg-90)/180.0))
			x1=int(x0+rmax*np.cos(np.pi*(deg-90)/180.0))
			grid=line(x0,y0,x1,y1,grid,2)
	if ViewCap[0]>0:
		grid[ViewCapMask==True]=1
		VC1=north+ViewCap[1]-ViewCap[0]/2.0
		VC2=north+ViewCap[1]+ViewCap[0]/2.0
		VC1=VC1*(np.pi/180)
		VC2=VC2*(np.pi/180)
		y1=int(y0-rmax*np.cos(VC1))
		x1=int(x0+rmax*np.sin(VC1))
		grid=line(x0,y0,x1,y1,grid,4)
		y1=int(y0-rmax*np.cos(VC2))
		x1=int(x0+rmax*np.sin(VC2))
		grid=line(x0,y0,x1,y1,grid,4)
	# Slopes line
	slope,aspect=slope_par
	if slope >0:
		grid[SlopeMask==False]=1
		grid=draw_slope(max_fov,slope,aspect,x0,y0,grid,5)
		aspect_r=aspect*(np.pi/180)
		slope_r=slope*(np.pi/180)
		ymn=-max_fov*np.sin(slope_r)-40
		ymx=-max_fov*np.sin(slope_r)+40
		x1=int(x0-ymn*np.sin(aspect_r)) # turn aspect
		y1=int(y0+ymn*np.cos(aspect_r))
		x2=int(x0-ymx*np.sin(aspect_r)) # turn aspect
		y2=int(y0+ymx*np.cos(aspect_r))
		#Normal Center
		y1=int(y0-max_fov*np.sin(slope_r)*np.cos(aspect_r)+0.05*max_fov*np.cos(aspect_r))
		x1=int(x0+max_fov*np.sin(slope_r)*np.sin(aspect_r)-0.05*max_fov*np.sin(aspect_r))
		y2=int(y0-max_fov*np.sin(slope_r)*np.cos(aspect_r)-0.05*max_fov*np.cos(aspect_r))
		x2=int(x0+max_fov*np.sin(slope_r)*np.sin(aspect_r)+0.05*max_fov*np.sin(aspect_r))
		grid=line(x1,y1,x2,y2,grid,5)
		x1=int(x0+(np.sin(aspect_r)*max_fov*np.sin(slope_r)-np.cos(aspect_r)*0.05*max_fov))
		y1=int(y0-(np.cos(aspect_r)*max_fov*np.sin(slope_r)+np.sin(aspect_r)*0.05*max_fov))
		x2=int(x0+(np.sin(aspect_r)*max_fov*np.sin(slope_r)+np.cos(aspect_r)*0.05*max_fov))
		y2=int(y0-(np.cos(aspect_r)*max_fov*np.sin(slope_r)-np.sin(aspect_r)*0.05*max_fov))
		grid=line(x1,y1,x2,y2,grid,5)
		# aspect Tag
		y1=int(y0-0.95*max_fov*np.cos(aspect_r))
		x1=int(x0+0.95*max_fov*np.sin(aspect_r))
		y2=int(y0-1.05*max_fov*np.cos(aspect_r))
		x2=int(x0+1.05*max_fov*np.sin(aspect_r))
		grid=line(x1,y1,x2,y2,grid,5)
	# LENS Limit
	grid=rasterCircle(y0,x0,max_fov,grid,7)
	# NORTH Tag
	y1=int(y0-0.95*max_fov*np.cos(north_r))
	x1=int(x0+0.95*max_fov*np.sin(north_r))
	y2=int(y0-1.05*max_fov*np.cos(north_r))
	x2=int(x0+1.05*max_fov*np.sin(north_r))
	grid=line(x1,y1,x2,y2,grid,7)
	# Center
	y1=int(y0-(-0.05)*max_fov*np.cos(north_r))
	x1=int(x0+(-0.05)*max_fov*np.sin(north_r))
	y2=int(y0-0.05*max_fov*np.cos(north_r))
	x2=int(x0+0.05*max_fov*np.sin(north_r))
	grid=line(x1,y1,x2,y2,grid,7)
	y1=int(y0-0.05*max_fov*np.sin(north_r))# turn aspect
	x1=int(x0-0.05*max_fov*np.cos(north_r))
	y2=int(y0+0.05*max_fov*np.sin(north_r))# turn aspect
	x2=int(x0+0.05*max_fov*np.cos(north_r))
	grid=line(x1,y1,x2,y2,grid,7)
	return grid

def showGrid(grid,skymask,north):
	empty=np.zeros(skymask.shape[0]*skymask.shape[1],dtype=np.uint8).reshape(skymask.shape)
	Rn=empty+0
	Gn=empty+0
	Bn=empty+0
	Rn[skymask==1]=200;Gn[skymask==1]=200;Bn[skymask==1]=255 #sky
	Rn[grid==1]=30+Bn[grid==1]/4;Gn[grid==1]=30+ Bn[grid==1]/4;Bn[grid==1]=30+Bn[grid==1]/4
	Rn[skymask==2]=0;Gn[skymask==2]=0;Bn[skymask==2]=0 #no Data
	Rn[skymask==3]=50;Gn[skymask==3]=50;Bn[skymask==3]=50 #masked Data
	Rn[grid>1]=0
	Gn[grid>1]=0
	Bn[grid>1]=0
	Gn[grid==2]=255
	Bn[grid==3]=255
	Bn[grid==4]=255;Gn[grid==4]=255
	Rn[grid==5]=255;Bn[grid==5]=255
	Rn[grid==6]=255;Gn[grid==6]=255
	Rn[grid==7]=255
	imgR = Image.fromarray(Rn)
	imgG = Image.fromarray(Gn)
	imgB = Image.fromarray(Bn)
	imgRGB = Image.merge('RGB', (imgR,imgG,imgB)) # color image
	imgRGB=imgRGB.rotate(north)
	#print north
	del Rn,Bn,Gn,imgR,imgG,imgB,empty
	return imgRGB
	
###########################################################################################
# IMAGE SEGMENT PIXEL INDEX EXTRACTION

def getBasicMaps(shape,center):
	x0,y0=center
	id=np.array(range(shape[1]*shape[0])).reshape(shape) 						# Pixel IDs
	x=np.array([range(shape[1])] * shape[0]).reshape(shape) 					# Pixel X Pos
	y=np.array([range(shape[0])] * shape[1]).reshape(shape[1],shape[0])		# Pixel Y Pos
	y=np.flipud(np.rot90(y))
	x[:,x0]=x0+1 																# Avoid divide by zero
	alphamap=(y-y0)/((x-x0)*1.0)												# Pixel angle
	alphamap=np.arctan(alphamap)
	alphamap=alphamap*(180/np.pi)
	alphamap=alphamap+90
	alphamap[y0,x0]=0
	alphamap[:,:x0]=alphamap[:,:x0]+180
	c=((x-x0)*(x-x0))+((y-y0)*(y-y0))											# circle Definition x^2+y^2
	return(id,alphamap,c,x,y)

def getSegmentAngles(nrings,nsectors,north,rings):
	alpha=360/(nsectors*1.0)
	zenith=[]
	azimuth=[]
	k=0
	for i in range(nrings):
		for j in range(nsectors):
			zenith.append((rings[k]+rings[k+1])/2.0)
			section_start=north+j*alpha
			section_stop=section_start+alpha
			if section_start<360.0 and section_stop>=360.0:
				section_stop=section_stop-360.0
			else:
				if section_start>=360 and section_stop>=360:
					section_start=section_start-360
					section_stop=section_stop-360
			azimuth.append((section_start+section_stop)/2.0)
		k=k+2
	zenith=np.array(zenith)*(np.pi/180)
	azimuth=np.array(azimuth)*(np.pi/180)
	return zenith,azimuth

def getSegments(center,nrings,nsectors,north,rings,max_fov):
	global BasicMaps
	print ('extracting segments')
	id,alphamap,c,x,y=BasicMaps
	shape=c.shape
	x0,y0=center
	idmap=np.zeros(shape[1]*shape[0],dtype=np.uint32).reshape(shape)			#SectionIndex
	alpha=360/(nsectors*1.0)
	#rings=[]
	#sectors=[]
	if nsectors>1:
		for i in range(nsectors):	
			section_start=north+i*alpha
			section_stop=section_start+alpha
			if section_start<360.0 and section_stop>=360.0:
				section_stop=section_stop-360.0
				section1=alphamap>=section_start
				section2=alphamap<section_stop
				idmap[section1+section2]=i
				#sectors.append(id[section1+section2])
			else:
				if section_start>=360 and section_stop>=360:
					section_start=section_start-360
					section_stop=section_stop-360
				section1=alphamap>=section_start
				section2=alphamap<section_stop
				idmap[section1&section2]=i
				#sectors.append(id[section1&section2])
	k=0
	for i in range(nrings):
		r1=LensCorr(max_fov,rings[k])
		r2=LensCorr(max_fov,rings[k+1])
		r1=r1*r1
		r2=r2*r2
		k=k+2
		c1=np.array(c<=int(r1),dtype=np.uint8)
		c2=c<=int(r2) 
		c1=c1+c2
		idmap[c1==1]=idmap[c1==1]+(i+1)*1000
		#rings.append(id[c1==1])
	# ignore pixel>max_fov
	idmap[c>(max_fov*max_fov)]=0
	idmap[idmap<nsectors]=0
	index=[]
	for i in range(1,nrings+1):
		for j in range(nsectors):
			index.append(i*1000+j)
	#blocks=np.unique(idmap)
	#blocks=blocks[blocks>0]
	blockID=[]
	for block in index:
		blockID.append(id[idmap==block])
	return blockID

def getSlopeMask(x,y,c,max_fov,slope,aspect):
	rx2=max_fov*max_fov
	slope_r=slope*(np.pi/180)
	aspect_r=aspect*(np.pi/180)
	if aspect>=0:
		x_rot=	(x-x0)*np.cos(aspect_r)+(y-y0)*np.sin(aspect_r) # turn aspect
		y_rot=	(y-y0)*np.cos(aspect_r)-(x-x0)*np.sin(aspect_r) # turn aspect
	else:
		x_rot=x
		y_rot=y
	tilty=np.cos(slope_r)#*np.cos(aspect_r)# slope
	ct=(x_rot)*(x_rot)+((y_rot)/tilty)*((y_rot)/tilty)
	slopeFOV=((ct<=rx2)&(y_rot>=0))+((c<rx2)&(y_rot<=0))
	return slopeFOV

def setSlope(slope_par,DataMask):
	global BasicMaps
	slope,aspect=slope_par
	slopemask=[]
	if slope>0.0:
			slopemask=getSlopeMask(BasicMaps[3],BasicMaps[4],BasicMaps[2],max_fov,slope,aspect)
			DataMask[slopemask==False]=3
			DataMask[BasicMaps[2]>(max_fov*max_fov)]=2
	return DataMask,slopemask

def setViewCap(ViewCap,north,DataMask):
	VCmask=[]
	if ViewCap[0]>0.0:
			VCmask=getViewCap(ViewCap,north)
			DataMask[VCmask==True]=3
	return DataMask,VCmask

def getViewCap(ViewCap,north):
	global BasicMaps
	VC,direction=ViewCap
	VC,direction=VC*1.0,direction*1.0
	startVC=north+direction-(VC/2.0)
	stopVC=north+direction+(VC/2.0)
	if startVC<0 and stopVC>0:
		startVC=360-startVC
		ViewCapMask=(BasicMaps[1]>=startVC) + (BasicMaps[1]<=stopVC)
	if startVC<=360 and stopVC>=360:
		stopVC=stopVC-360
		ViewCapMask=(BasicMaps[1]>=startVC) + (BasicMaps[1]<=stopVC)
	else:
		if startVC>=360:	startVC=startVC-360
		if startVC<0:	startVC=360-startVC
		if stopVC>=360: stopVC=stopVC-360
		if stopVC<0: stopVC=360-stopVC
		ViewCapMask=(BasicMaps[1]>=startVC) & (BasicMaps[1]<=stopVC)
	return ViewCapMask

###########################################################################################
# LENS ADJUSTMENT

def setLens(LensNumber):
	LensName=[]
	LensInfo=[]
	LensPar=[]
	LensName.append("Linear Lens")
	LensInfo.append("Linear 0-90 degree interpolation")
	LensPar.append([0,0,0,0,0])
	LensName.append("Sigma 4.5mm")
	LensInfo.append("Sigma 4.5mm circular fisheye for small-frame reflex")
	LensPar.append([0.69513,0.03835,-0.048128,0,0])
	LensName.append("Sigma 8mm")
	LensInfo.append("Sigma 8mm SLR fisheye lens")
	LensPar.append([0.75276,-0.073937,0,0,0])
	LensName.append("Nikon FC-E8")
	LensInfo.append("Nikon fisheye adapter / Coolpix")
	LensPar.append([0.681,-0.028253,0,0,0])
	LensName.append("Nikon FC-E9")
	LensInfo.append("Nikon fisheye adapter / Coolpix")
	LensPar.append([0.6427,0.0346,-0.024491,0,0])
	LensName.append("Nikkor 8mm")
	LensInfo.append("Nikkor 8mm fisheye lens")
	LensPar.append([0.9192,-0.1792,-0.000443,0,0])
	LensName.append("Nikkor OP 10mm")
	LensInfo.append("Nikkor 10mm fisheye lens")
	LensPar.append([1.0168,-0.0573,-0.117603,0,0])
	LensName.append("Soligor Fish Eye")
	LensInfo.append("Soligor fisheye adapter / Sony DCW")
	LensPar.append([0.677923,-0.029481,-0.022084,0.041495,-0.016644])
	LensName.append("Raynox DCR-CF185")
	LensInfo.append("Raynox fisheye adapter / Fuji FinePix")
	LensPar.append([0.5982,0.024459,0,0,0])
	print ("LENS: " +LensName[LensNumber]+": "+LensInfo[LensNumber])
	return LensPar[LensNumber]

def LensCorr(Lens_fov_radius,T):
	global LensPar 
	if LensPar== [0,0,0,0,0]:
		Lens_fov_degree=90
		pixelradius=(Lens_fov_radius/(Lens_fov_degree*1.0))*T
		return(pixelradius)
	else:
		T=T*(np.pi/180)
		pixelradius=LensPar[0]*T + LensPar[1]*np.power(T,2) + LensPar[2]*np.power(T,3) + LensPar[3]*np.power(T,4) + LensPar[4]*np.power(T,5)
		pixelradius=pixelradius*Lens_fov_radius
	return(pixelradius)

###########################################################################################
# BASIC MATH FUNCTIONS

def linreg(X, Y):
	#Summary Linear regression of y = ax + b
	N = len(X)
	Sx = Sy = Sxx = Syy = Sxy = 0.0
	#for x, y in map(None, X, Y): # Python 2.7
	for x, y in zip_longest(X,Y):
	
		Sx = Sx + x
		Sy = Sy + y
		Sxx = Sxx + x*x
		Syy = Syy + y*y
		Sxy = Sxy + x*y
	det = Sxx * N - Sx * Sx
	a, b = (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det
	meanerror = residual = 0.0
	#for x, y in map(None, X, Y):
	for x, y in zip_longest(X,Y):
		meanerror = meanerror + (y - Sy/N)**2
		residual = residual + (y - a * x - b)**2
	RR = 1 - residual/meanerror
	ss = residual / (N-2)
	Var_a, Var_b = ss * N / det, ss * Sxx / det
	return a, b, RR

###########################################################################################
# TRANSMISSION EXTRACTION

def getTransmission(data,segments):
	data=data.flatten()
	transmission=[]
	emptysegment=[]
	for i in range(len(segments)):
		segmentpixel=data[segments[i]]
		ignore= len(segmentpixel[segmentpixel>1])
		if len(segmentpixel)==ignore: # Full Segment is ignored...
			t=np.exp(1)
		else:			
			sky=len (segmentpixel[segmentpixel==1])
			vegetation=len (segmentpixel[segmentpixel==0])
			if sky==0:
				print ('warning: segment ' + str(i) + ' transmission is 0%')
				emptysegment.append(i)
				sky=0.5 # Avoid Transmission= 0, set 0.5 pixel as sky
			t=sky/(sky+vegetation*1.0)
		transmission.append(t)	
	return transmission,emptysegment

def getLeafTransmission(ImageTransmission,WoodTransmission):	return ImageTransmission+(1-WoodTransmission)

def getGapfraction(transmission):	return -np.log(transmission)

def Segment_linAverage(nrings, nsectors, transmission,zenith):
	#lang and Xiang 1987
	lmt=[]
	for i in range(nrings):
		rm=np.mean(transmission[i*nsectors:((i+1)*nsectors)])
		lmt.append(rm)
	lmt=-np.log(np.array(lmt))
	mzenith=[]
	for i in (np.array(range(nrings))*nsectors):
		mzenith.append(zenith[i])
	return lmt,mzenith

def Segment_logAverage(nrings, nsectors, transmission,zenith):
	#lang and Xiang 1987
	lmt=[]
	for i in range(nrings):
		rsum=np.sum(np.log(transmission[i*nsectors:((i+1)*nsectors)]))
		lmt.append(rsum)
	lmt=-np.array(lmt)/(nsectors*1.0)
	mzenith=[]
	for i in (np.array(range(nrings))*nsectors):
		mzenith.append(zenith[i])
	return lmt,mzenith

###########################################################################################
# IMAGE ANALYSIS

def getSkyViewFactor(nsectors,nrings,transmission,zenith,rings):
	SVF=0
	for n in range(nsectors):
		gap_zenith=[]
		gap_trans=[]
		for i in (np.array(range(nrings),dtype=np.uint16)*nsectors+n):
			gap_zenith.append(zenith[i])
			gap_trans.append(transmission[i])
		svf=0
		k=0
		for i in range(nrings):
			svf=svf+2*((rings[k+1]-rings[k])*(np.pi/180.0))*gap_trans[i]*np.sin(gap_zenith[i])
			k=k+2
		SVF=SVF+svf
	SVF=SVF/(nsectors*1.0)
	return SVF

def ClumpingIndex_Lang(L_log,L_lin): return L_log/(L_lin*1.0)

################################
# LAI CALCULATION

def LAI_Miller(gaps,gap_zenith,dt):
	Ks=0
	for i in range(len(gaps)):
		K=gaps[i]*np.cos(gap_zenith[i])
		Ks=Ks+K*np.sin(gap_zenith[i])*dt[i]
	L=(2*Ks)
	return L

def get_LAI_Miller(nrings,nsectors,gapfraction,zenith,rings):
	#Miller (1967) # LAI within Rings
	LAI=0
	dt=[]
	k=0
	for i in range(nrings):
		dt.append((rings[k+1]-rings[k])*(np.pi/180.0))
		k=k+2
	for n in range(nsectors):
		gap_zenith=[]
		gaps=[]
		for i in (np.array(range(nrings))*nsectors+n):
			if not gapfraction[i] < 0:
				gap_zenith.append(zenith[i])
				gaps.append(gapfraction[i])
		L=LAI_Miller(gaps,gap_zenith,dt)
		LAI=LAI+L
		#print n+1,L
	LAI=LAI/(nsectors*1.0)
	return LAI
	
##################

def LAI_Miller_LiCor_general(gaps,gap_zenith,dt):
	Ks=0
	for i in range(len(gaps)):
		K=gaps[i]*np.cos(gap_zenith[i])
		Ks=Ks+K*np.sin(gap_zenith[i])*dt[i]
	L=(2*Ks)
	return L

def get_LAI_Miller_LiCor_general(nrings,nsectors,gapfraction,zenith,rings,fov):
	#Miller (1967) LiCor generalized
	LAI=0
	k=0
	dt=[]
	for i in range(nrings):
		dt.append((rings[k+1]-rings[k])*(np.pi/180.0))
		k=k+2
	dt[-1]=dt[-1]+((90-fov)*(np.pi/180))
	for n in range(nsectors):
		gap_zenith=[]
		gaps=[]
		for i in (np.array(range(nrings))*nsectors+n):
			if not gapfraction[i] < 0:
				gap_zenith.append(zenith[i])
				gaps.append(gapfraction[i])
		L=LAI_Miller_LiCor_general(gaps,gap_zenith,dt)
		LAI=LAI+L
	LAI=LAI/(nsectors*1.0)
	return LAI

##################

def LAI_LiCor(gapfraction,zenith):
	Ks=0
	K=gapfraction[0]*np.cos(zenith[0])
	Ks=Ks+K*0.034
	K=gapfraction[1]*np.cos(zenith[1])
	Ks=Ks+K*0.104
	K=gapfraction[2]*np.cos(zenith[2])
	Ks=Ks+K*0.160
	K=gapfraction[3]*np.cos(zenith[3])
	Ks=Ks+K*0.218
	K=gapfraction[4]*np.cos(zenith[4])
	Ks=Ks+K*0.484
	L=2*Ks
	return L

def get_LAI_LiCor(skymask,LiCorSegments):
	#LiCor original
	LiCorZenith=np.array([7.0,23.0,38.0,53.0,68.0])*(np.pi/180)
	transmission,es=getTransmission(skymask,LiCorSegments)
	gaps=-np.log(transmission)
	LAI=LAI_LiCor(gaps,LiCorZenith)
	return LAI

##################

def LAI_Lang(gaps,gap_zenith):
		K=gaps*np.cos(gap_zenith)
		m,z,RR=linreg(gap_zenith,K)
		a = 56.81964; b = 46.84833; c = -64.62133; d = -158.6914; e = 522.0626; f = 1008.149
		MTA = a + b*m + c*np.power(m,2) + d*np.power(m,3) + e*np.power(m,4) + f*np.power(m,5) #Mean Tilt Angle
		L=2*(z+m)
		return L,MTA

def get_LAI_Lang(nrings,nsectors,gapfraction,zenith):
	#Lang 1987
	LAI=0
	MTA=0
	for n in range(nsectors):
		gap_zenith=[]
		gaps=[]
		for i in (np.array(range(nrings))*nsectors+n):
			if not gapfraction[i] < 0:
				gap_zenith.append(zenith[i])
				gaps.append(gapfraction[i])
		L,A=LAI_Lang(gaps,gap_zenith)
		LAI=LAI+L
		MTA=MTA+A
		#print n,L,A
	LAI=LAI/(nsectors*1.0)
	MTA=MTA/(nsectors*1.0)
	return LAI,MTA

##################

def LAI_NormanCampbell_fnk(Z,X): return np.sqrt(X*X+Z*Z)/(X+1.774*np.power(X+1.182,-0.733))

def LAI_NormanCampbell(gaps,gap_zenith):
	dx=0.01
	z=np.tan(np.array(gap_zenith))
	t=-np.array(gaps)
	xmax=10.0
	xmin=0.1
	x=1.0
	while (xmax-xmin)>.01:
		s1=0.0
		s2=0.0
		s3=0.0
		s4=0.0
		for i in range(len(gaps)):
			tz=z[i]
			kb=LAI_NormanCampbell_fnk(tz,x)
			dk=LAI_NormanCampbell_fnk(tz,x+dx)-kb
			s1=s1+kb*t[i]
			s2=s2+kb*kb
			s3=s3+kb*dk
			s4=s4+dk*t[i]
		f=s2*s4-s1*s3
		if f<0:
			xmin=x
		else:
			xmax=x
		x=(xmax+xmin)/2
	L=-s1/s2 # LAI
	rVH=x    # ratio vertical to horizontal projections
	mla=90*(0.1+0.9*np.exp(-0.5*x)) # mean leaf angle
	#print "Zenith\t MeasuredT\tPredictedT"
	#for i in range(len(gaps)):
	#	print ' %5.3f\t%5.2f\t\t%5.7f'%(np.arctan(z[i])*(180/np.pi),np.exp(t[i]),np.exp(-LAI_NormanCampbell_fnk(z[i],x)*L))
	return L,rVH,mla

def get_LAI_NormanCampbell(nrings,nsectors,gapfraction,zenith):
	# Norman Campbell: ELLIPSOIDAL LEAF ANGLE DISTRIBUTION
	#Norman and Campbell, 1989
	# Uses Original algotrithm for nsectros=1, calculates azimutal means for  nsectros>1
	LAI=0
	RVH=0
	MLA=0
	for n in range(nsectors):
		gap_zenith=[]
		gaps=[]
		for i in (np.array(range(nrings))*nsectors+n):
			if not gapfraction[i] < 0:
				gap_zenith.append(zenith[i])
				gaps.append(gapfraction[i])
		L,rVH,mla=LAI_NormanCampbell(gaps,gap_zenith)
		#print L,rVH,mla
		LAI=LAI+L
		RVH=RVH+rVH
		MLA=MLA+mla
	LAI=LAI/(nsectors*1.0)
	RVH=RVH/(nsectors*1.0)
	MLA=MLA/(nsectors*1.0)
	return LAI,RVH,MLA

###########################################################################################
# PARAMETER INITIALIZATION

def initializeParameters(fov,deg_per_ring,nrings,rings,Lfov_degree,north,slope_par,ring_mode="Angle"):
	slope_par[1]=slope_par[1]+north
	if slope_par[1]>=360:
		slope_par[1]=slope_par[1]-360
	if fov<0:
		fov=deg_per_ring*nrings
		if fov>Lfov_degree:
			deg_per_ring=Lfov_degree/(nrings*1.0)
			fov=Lfov_degree
	else:
		if fov>Lfov_degree:
			fov=Lfov_degree
		deg_per_ring=fov/(nrings*1.0)	
	if len(rings)<nrings:
		rings=[]
		if ring_mode=="Area":
			fov_rad=fov*(np.pi/180)
			theta_inner=0
			for r in range(nrings):
				theta_outer=2*np.arccos(np.cos(theta_inner/2)+(np.cos(fov_rad/2)/nrings)-1/(nrings*1.0))
				rings.append(theta_inner*(180/np.pi))
				rings.append(theta_outer*(180/np.pi))
				theta_inner=theta_outer
		else:
			for r in range(nrings):
				rings.append(r*deg_per_ring)
				rings.append((r+1)*deg_per_ring)
	else:
		fov=rings[-1]
	return fov,rings,slope_par

###########################################################################################
# ANALYSE LAI OF SINGLE MASK 

def getLAI(name,skymask,parameter,savegrid,showgrid):
	global BasicMaps
	print ('calculating ...\n')
	shape,nrings,nsectors,rings,north,fov,slope_par,ViewCap,segments,zenith,azimuth,LiCorSegments,LiCorGrid=parameter
	datamask=np.zeros(shape[0]*shape[1],dtype=np.uint8).reshape(shape)
	datamask=datamask+skymask
	datamask,SlopeMask=setSlope(slope_par,datamask)
	datamask,ViewCapMask=setViewCap(ViewCap,north,datamask)
	transmission,emptysegment=getTransmission(datamask,segments)
	gapfraction=getGapfraction(transmission)
	if showgrid==True or not savegrid=="":
		grid=drawGridOutupt(shape,center,nrings,nsectors,north,fov,max_fov,rings,ViewCap,ViewCapMask,slope_par,SlopeMask)
		for es in emptysegment:
			shape=grid.shape
			grid=grid.flatten()
			grid[segments[es]]=4	
			grid=grid.reshape(shape)
	if showgrid==True:
		showGrid(grid,skymask,north).show()
		#showGrid(LiCorGrid,datamask).show()
	if not savegrid=="":
		showGrid(grid,skymask,north).save(os.path.join(savegrid,name.split('/')[-1].split('.')[0]+'_grid.jpg'))
		#showGrid(LiCorGrid,datamask).save(name.split('.')[0]+'_LiCorgrid.jpg')
	#Calculate Values
	SVF=getSkyViewFactor(nsectors,nrings,transmission,zenith,rings)
	LAI_norman,rHV_norman,MLA_norman=get_LAI_NormanCampbell(nrings,nsectors,gapfraction,zenith)
	LAI_lang,MTA_Lang=get_LAI_Lang(nrings,nsectors,gapfraction,zenith)
	LAI_miller=get_LAI_Miller(nrings,nsectors,gapfraction,zenith,rings)
	LAI_licor_gen=get_LAI_Miller_LiCor_general(nrings,nsectors,gapfraction,zenith,rings,fov)
	if nsectors>1:
		linGF,mzenith=Segment_linAverage(nrings, nsectors, transmission,zenith)
		linm_LAI_norman,linm_rHV_norman,linm_MLA_norman=get_LAI_NormanCampbell(nrings,1,linGF,mzenith)
		linm_LAI_lang,linm_MTA_Lang=get_LAI_Lang(nrings,1,linGF,mzenith)
		linm_LAI_miller=get_LAI_Miller(nrings,1,linGF,mzenith,rings)
		linm_LAI_licor_gen=get_LAI_Miller_LiCor_general(nrings,1,linGF,mzenith,rings,fov)
		
		logGF,mzenith=Segment_logAverage(nrings, nsectors, transmission,zenith)
		logm_LAI_norman,logm_rHV_norman,logm_MLA_norman=get_LAI_NormanCampbell(nrings,1,logGF,mzenith)
		logm_LAI_lang,logm_MTA_Lang=get_LAI_Lang(nrings,1,logGF,mzenith)
		logm_LAI_miller=get_LAI_Miller(nrings,1,logGF,mzenith,rings)
		logm_LAI_licor_gen=get_LAI_Miller_LiCor_general(nrings,1,logGF,mzenith,rings,fov)
		
		CI_LAI_norman=ClumpingIndex_Lang(logm_LAI_norman,linm_LAI_norman)
		CI_LAI_lang=ClumpingIndex_Lang(logm_LAI_lang,linm_LAI_lang)
		CI_LAI_miller=ClumpingIndex_Lang(logm_LAI_miller,linm_LAI_miller)
		CI_LAI_licor_gen=ClumpingIndex_Lang(logm_LAI_licor_gen,linm_LAI_licor_gen)
	else:
		linm_LAI_norman=0
		linm_LAI_lang=0
		linm_LAI_miller=0
		linm_LAI_licor_gen=0
		logm_LAI_norman=0
		logm_LAI_lang=0
		logm_LAI_miller=0
		logm_LAI_licor_gen=0
		CI_LAI_miller=0
		CI_LAI_lang=0
		CI_LAI_licor_gen=0
		CI_LAI_norman=0
		linm_MTA_Lang=0
		linm_rHV_norman=0
		linm_MLA_norman=0
		logm_MTA_Lang=0
		logm_rHV_norman=0
		logm_MLA_norman=0
		
	LAI_licor=get_LAI_LiCor(datamask,LiCorSegments)
	LAI=[
				nrings,
				nsectors,
				len(emptysegment),
				np.mean(transmission),
				SVF,
				LAI_norman,
				LAI_lang,
				LAI_miller,
				LAI_licor_gen,
				LAI_licor,
				linm_LAI_norman,
				linm_LAI_lang,
				linm_LAI_miller,
				linm_LAI_licor_gen,
				logm_LAI_norman,
				logm_LAI_lang,
				logm_LAI_miller,
				logm_LAI_licor_gen,
				CI_LAI_norman,
				CI_LAI_lang,
				CI_LAI_miller,
				CI_LAI_licor_gen,
				MTA_Lang,
				rHV_norman,
				MLA_norman,
				linm_MTA_Lang,
				linm_rHV_norman,
				linm_MLA_norman,
				logm_MTA_Lang,
				logm_rHV_norman,
				logm_MLA_norman
				]
	return LAI

###########################################################################################
# PROCESS FILELIST AND WRITE RESULT FILE

def runCalculations(filelist,resultfile,SeriesSettings,AnalysisSettings):
	# Unpack Parameters
	shape,center,LensPar,Lfov_degree,max_fov,resultpath,resultfile,GRIDpath=SeriesSettings
	north,fov,nrings,nsectors,rings,slope,aspect,ViewCap,ring_mode=AnalysisSettings
	slope_par=[slope*1.0,aspect*1.0]
	fov,rings,slope_par=initializeParameters(fov,deg_per_ring,nrings,rings,Lfov_degree,north,slope_par,ring_mode)
	# Initialize GRIDS
	LiCorRings=[0.0,12.3,16.7,28.6,32.4,43.4,47.3,58.1,62.3,74.1]
	LiCorSegments=getSegments(center,5,1,north,LiCorRings,max_fov)
	LiCorGrid=drawGrid(shape,center,5,1,north,74.1,max_fov,LiCorRings,(0,0))
	# PREPARE OUTOUT
	f = open(resultfile,'w')
	header=["image","nrings", "nsectors", "empty_seg", "transmission", "SkyViewFactor", "LAI_norman", "LAI_lang", "LAI_miller", "LAI_licor_gen", "LAI_licor",	"linm_LAI_norman", "linm_LAI_lang", "linm_LAI_miller", "linm_LAI_licor_gen", "logm_LAI_norman", "logm_LAI_lang", "logm_LAI_miller", "logm_LAI_licor_gen",	"CI_LAI_norman", "CI_LAI_lang", "CI_LAI_miller", "CI_LAI_licor_gen",
	"MTA_Lang", "rHV_norman", "MLA_norman", "linm_MTA_Lang", "linm_rHV_norman", "linm_MLA_norman", "logm_MTA_Lang", "logm_rHV_norman", "logm_MLA_norman" ]
	fline=""
	for col in header:
		fline=fline +str(col)+";"
	fline=fline.rstrip(';')+'\n'
	f.write(fline)
	if nsectors==1:
		segments=getSegments(center,nrings,nsectors,north,rings,max_fov)
	# MAKE LAI ANALYSIS FOR ALL FILES
	currentset="no set"
	for file in filelist:
		# Site Set Processing (for excluding Sun Pixels)
		setname = os.path.split(file)[0]
		if not currentset==setname:
			setpar=readSetParameter(setname)
			currentset=setname
		print ('processing image ' + file)
		north=getParameter(file)[2]
		inv_pix=getPixelMask(setpar,north)	
		if nsectors>1:
			segments=getSegments(center,nrings,nsectors,north,rings,max_fov)
		zenith,azimuth=getSegmentAngles(nrings,nsectors,north,rings)
		parameter=(shape,nrings,nsectors,rings,north,fov,slope_par,ViewCap,segments,zenith,azimuth,LiCorSegments,LiCorGrid)
		skymask=getSkyMask(file,1,max_fov,True,imgcenter,inv_pix)
		LAI=getLAI(file,skymask,parameter,GRIDpath,False)
		del skymask
		f.write(file+';')
		fline=""
		for val in LAI:
			fline=fline +str(val)+";"
		fline=fline.rstrip(';')+'\n'
		f.write(fline)
	f.close()

#########################################################################
#########################################################################
# A Python program to calculate LAI from Hemishperical photographs
#########################################################################
import os,sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from itertools import zip_longest

print ('INITIALIZE PROGRAM:')

def listallfiles(basePath):
	basePath=basePath.replace("\\","/")
	if os.path.exists(basePath)==False:
		print ("Path does not exits")
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
	
def readfilelist(filelistname):
	filelist=[]
	flfile= open(filelistname,'r')
	for line in flfile.readlines():
		line=line.strip()
		line=line.replace("\\","/")
		filelist.append(line)
	return filelist

def getParameter(imagename,silent=False):
	parfile= os.path.splitext(imagename)[0]+".par"
	if os.path.exists(parfile)==False:
		if not silent:
			print ("no metadata: ("+ parfile.split("/")[-1]+"): setting north to 0.0")
		center=(0,0)
		radius=0
		north=0.0
		burn_center=(0,0)
		burn_radius=0
	else:
		print ("reading metadata from "+ os.path.split(parfile)[-1])
		pfile= open(parfile,'r')
		parline=pfile.readlines()[1] # remove header
		pfile.close()
		parline=parline.strip()
		parline=parline.split(';')
		#SITE;OBS;LAT;LON;ALT;TIME;CENTER;RADIUS;NORTH;WOOD #Optional ,BX,BY,BR
		center=parline[6]
		centerX,centerY = center.strip("[]").split(',')
		center= int(centerX),int(centerY)
		radius=int(parline[7])
		north=float(parline[8])
		burn_centerX,burn_centerY,burn_radius= ("","","")
		if len(parline)>10:
			burn_centerX,burn_centerY,burn_radius= int(parline[10]),int(parline[11]),int(parline[12])
		#centerX,centerY,radius,north,woodimage,burn_centerX,burn_centerY,burn_radius=parline
		if burn_centerX=="": burn_centerX=0
		if burn_centerY=="": burn_centerY=0
		burn_center=int(burn_centerX),int(burn_centerY)
		if burn_radius=="":
			burn_radius=0
		burn_radius=int(burn_radius)
	return center,radius,north,burn_center,burn_radius


def readSetParameter(setname):
	print ("collecting site-set data")
	setlist=listallfiles(setname)
	setpar=[]
	for s in setlist:
		setpar.append(getParameter(s))
	print ("")
	return setpar


def getPixelMask(setpar,inorth):
	inv_pix=[]
	for s in setpar:
		center,radius,north,burn_center,burn_radius=s
		if not burn_radius==0:
			rotangle=(inorth-north)*(np.pi/180)
			new_burn_center = int(np.cos(rotangle) * (burn_center[0]) - np.sin(rotangle) * (burn_center[1])),int(np.sin(rotangle) * (burn_center[0]) + np.cos(rotangle) * (burn_center[1]))
			cp=getCirclePix(new_burn_center[0],new_burn_center[1],burn_radius)
			inv_pix.extend(cp)
	inv_pix=list(set(inv_pix))
	return inv_pix

#################################################################################################################
# MAIN EXECUTION
#################################################################################################################
basePath=os.getcwd()

if len(sys.argv)<3:
	print ("CGA.py [imagepath] [outpath]")

resultpath=os.path.join(sys.argv[2],"out")

if len(sys.argv)> 1:
	print ('reading path '+ sys.argv[1])
	basePath=sys.argv[1]
if len(sys.argv)> 2:
	resultpath=sys.argv[2]

filelist=listallfiles(basePath)

print ('initialize center, radius')
center,max_fov,north=getParameter(filelist[0],True)[0:3]
i=0

while center==(0,0) and i< len(filelist):
	center,max_fov,north=getParameter(filelist[i],True)[0:3]
	i=i+1

if center==(0,0):
	print ("WARNING: No parameter file found --- Image center is estimated and may generate accurate results")
	sourceImage=getRGB(filelist[0],[0,0],0,square=False)
	fullshape= sourceImage[0].shape
	center=(int(fullshape[1]/2),fullshape[0]/2)
	max_fov=int(0.75*fullshape[1]/2)

imgcenter=[center[0],center[1]]
print ("center: "+ str(center))
print ("radius: "+ str(max_fov))
print ('initialize images')
sourceImage=getRGB(filelist[0],[0,0],0,square=False)
fullshape= sourceImage[0].shape
sourceImage=getRGB(filelist[0],imgcenter,max_fov,square=True)
center=[max_fov,max_fov]
shape= sourceImage[0].shape
del sourceImage

#################################################################################
# Setup Basic Parameters

USE_EXISTING_BINARYMASKS=False

print ('initialize lens')
LensPar=setLens(3)
Lfov_degree=90.0			# maximal field of view of the lens

# Analysis Settings
fov=80						# if fov<0, gets calculated fov=deg_per_ring*nrings
deg_per_ring=40				#gets calculated, except fov<0 (see above)
nrings=5
nsectors=1
rings=[]					#[0,10,20,30,40,50] define exact rings, set nrings above to 0
ViewCap=[0,0]				#[75.0,130.0]
ring_mode= "Angle" 			#"Angle" or "Area" divide view into equal angle or area rings

# OUTPUT Paths
# resultpath set as parameter above
BINpath= os.path.join(resultpath,"BINS")
GRIDpath=os.path.join(resultpath,"GRIDS")
resultfile=os.path.join(resultpath,"Results.txt")

#################################################################################
if USE_EXISTING_BINARYMASKS==True: 
	print ("Using existing image segmentation")
else:
	print ("Initialize image segmentation")
# initialize individual image settings
north=0 # will be set individually from parameter file 
slope=0 #(creation of parameter in ImageRot.py is not supported yet)
aspect=0 #(creation of parameter in ImageRot.py is not supported yet)
print ('initialize basic maps')
BasicMaps=getBasicMaps(shape,center)
print ('initialize settings')
print ("\tfield of view: " +str(fov))
print ("\trings: " +str(nrings)+", equal "+ ring_mode)
print ("\tsectors: " +str(nrings))
Analysis_Settings=north,fov,nrings,nsectors,rings,slope,aspect,ViewCap,ring_mode
Series_Settings=shape,center,LensPar,Lfov_degree,max_fov,resultpath,resultfile,GRIDpath
if os.path.exists(resultpath)==False:
	print ("creating output directory")
	os.mkdir(resultpath)
if os.path.exists(BINpath)==False:
	print ("creating output directory")
	os.mkdir(BINpath)
if os.path.exists(GRIDpath)==False:
	print ("creating output directory")
	os.mkdir(GRIDpath)
print ('\nRUNNING ANALYSIS\n')
runCalculations(filelist,resultfile,Series_Settings,Analysis_Settings)


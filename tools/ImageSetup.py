#Image Assignment:
#
#	once:
#		define center
#		define radius
#	once per Series
#		define north, referencepoint
#	on individual picture
#		define referencepoint
#		
#	calculate:
#			|    
#			|	*
#			|  /
#			|a/
#			|/
#			|
#			angle from 0 to reference point for each image
#			angle from north to reference point for reference image
#			angle from 0 to north for each image
#			
#			requires:
#			per_folder
#			Actual_Image
#			current_Wood_Reference
#			current_North_Reference
#			
#			save 
#	Set 	image	center		radius	rot_ref,	north_ref	woodref	north	north
#		001	image1	312,312;	400;	10;			image3;		image1;			30
#		001	image2	312,312;	400;	70;			image3;		image1;			-10
#		001	image3	312,312;	400;	20;			40;			image1;			0
#
#make parameterfile
#global: center,radius
#file, Woodland_reference,north,set
#file, Woodland_reference,north,set
#file, Woodland_reference,north,set
#file, Woodland_reference,north,set
#file, Woodland_reference,north,set

import pygtk
import gtk
import sys, os
import Image
import ImageDraw
import numpy as np
import StringIO

SourceImage=0
DrawImage=0
FinalImage=0

Zoomfactor=1
Action=0
# Action 0: do nothing
# Action 1: set Center
# Action 2: set Radius
# Action 3: set North
# Action 4: set Reference
# Action 5: Mask Burn (SUN)
#treestore = gtk.ListStore('gchararray','gboolean')
treestore = gtk.ListStore('gchararray')
North_liststore = gtk.ListStore('gchararray')
North_list=[]
Wood_liststore = gtk.ListStore('gchararray')
Wood_list=[]

CurrentImage=""
North_Image=""
North_Angle=""
North_Reference_Point=""
North_Reference_Angle=""
RefAngle=""
Refxy=""
center=(200,200)
radius=100
WoodRef=""

Burn_center=("","")
Burn_radius=0

CalcNorthAngle=""

allfiles=[]
allfilenames=[]

Data=[]


class ImgRot:
	def __init__(self):
		self.builder = gtk.Builder()
		self.builder.add_from_file("ImageSetup.glade")
		self.builder.connect_signals(self)
		self.win =  self.builder.get_object('MainWin')
		self.path = None
		#self.SetStatusbar('(c) D.Basler 2011')
		self.win.show()
		self.InitializeTree()
		self.InitializeNorth()
		self.InitializeWood()
	
	def run(self):
		try:
			gtk.main()
		except KeyboardInterrupt:
			pass
	
	def quit(self):
		gtk.main_quit()
		sys.exit()
		
	
	def on_buttonLoadImages_clicked(self, action, *args):
		global allfiles,allfilenames,center,radius
		#allfiles,allfilenames=self.readfilelist("filelist.txt") # TEST only , read files from Filelist.txt
		allfiles,allfilenames=self.listallfiles()
		self.prepareEmptyDataFile()
		self.InitializeTreeItems()
		self.loadImage(allfiles[0],allfilenames[0])
		size=SourceImage.size
		center=[size[0]/2,size[1]/2]
		radius=min(center)
		self.builder.get_object('entryX').set_text(str(center[0]))
		self.builder.get_object('entryY').set_text(str(center[1]))
		self.builder.get_object('entryRadius').set_text(str(radius))
		self.loadImage(allfiles[0],allfilenames[0])
		
	def readfilelist(self,filelistname): ### FOR TESTNG ONLY
		filelist=[]
		filenames=[]
		flfile= open(filelistname,'r')
		for line in flfile.readlines():
			line=line.strip()
			line=line.replace("\\","/")
			filelist.append(line)
			filenames.append(line.split('/')[-1])
		return filelist,filenames
		
	def listallfiles(self):
		basePath=self.builder.get_object('entryImagePath').get_text()
		basePath=basePath.replace("\\","/")
		if os.path.exists(basePath)==False:
			print "Path does not exits"
			return
		#if not basePath[-1]=="/":basePath=basePath+"/"
		filelist=[]
		filenames=[]
		for root, dirs, files in os.walk(basePath):
			for f in files:
				f=f.lower()
				if f.endswith('.jpg') or f.endswith('.jpeg'):
					file=os.path.join(root,f)
					file=file.strip()
					file=file.replace("\\","/")
					filelist.append(file)
					filenames.append(file.split('/')[-1])
		return filelist,filenames
	
	def prepareEmptyDataFile(self):
		global allfiles,allfilenames,Data
		Data=[]
		for i in range(len(allfiles)):
			Data.append([allfiles[i],allfilenames[i],"","","","","","","","","",""])
	
	def on_buttonSave_clicked(self, action, *args):
		self.saveData("Rotations.txt")
	
	def saveData(self,filename):
		global Data,allfiles
		self.storeData()
		f=open(filename,'w')
		header="Path;Image;center;radius;RefXY;RefAngle;North_Image;North_Angle;CalcNorthAngle;WoodRef;BurnCenter;BurnRadius\n"
		f.write(header)
		for i in range(len (allfiles)):
			if os.path.exists(allfiles[i]):
				line=""
				for j in range(12):
					line=line+str(Data[i][j])+";"
				line=line[0:len(line)-1]+"\n"
				f.write(line)
		print "saved data"
	
	def on_buttonSaveParameter_clicked(self, action, *args):
		self.saveParameters()
		
	def saveParameters(self):
		global Data,allfiles,center,radius
		for i in range(len (allfiles)):
			if os.path.exists(allfiles[i]):
				if not Data[i][8]=="":
					filename=Data[i][0].split('.')[0]+".par"
					f=open(filename,'w')
					line=str(center[0])
					line=line+";"+str(center[1])
					line=line+";"+str(radius)
					line=line+";"+str(Data[i][8])
					line=line+";"+str(Data[i][9]==Data[i][1])
					if not Data[i][10]=="":
						line=line+";"+str(Data[i][10][0])
						line=line+";"+str(Data[i][10][1])
						line=line+";"+str(Data[i][11])
					else:
						line=line+";0;0;0"
					f.write(line)
					f.close()
		print "saved parameters"
		
	def storeData(self):
		global center,radius,North_Image,North_Angle,Refxy,RefAngle,WoodRef,CurrentImage,North_Reference_Point,Burn_center,Burn_radius
		#print "stored "+CurrentImage
		n=allfilenames.index(CurrentImage)
		Data[n][0]=allfiles[n]
		Data[n][1]=CurrentImage
		Data[n][2]=center
		Data[n][3]=radius
		Data[n][4]=Refxy
		Data[n][5]=RefAngle		
		Data[n][6]=North_Image
		Data[n][7]=North_Angle
		Data[n][8]=CalcNorthAngle
		Data[n][9]=WoodRef
		Data[n][10]=Burn_center
		Data[n][11]=Burn_radius

	def on_buttonOpen_clicked(self, action, *args):
		self.openData("Rotations.txt")

	def openData(self,filename):
		global CurrentImage,Data,allfilenames,allfiles,North_list,Wood_list,North_liststore,Wood_liststore,center,radius,Burn_center,Burn_radius
		Data=[]
		North_list=[]
		Wood_list=[]
		files=[]
		filenames=[]	
		f=open(filename,'r')
		lines=f.readlines()
		lines.pop(0) # drop header
		for line in lines:
			line=line.strip()
			line=line.split(";")
			# format elements
			if not line[2]=="":
				line[2]= line[2].strip("()")
				line[2]= line[2].strip("[]")
				line[2]= line[2].split(",")
				line[2][0]=int(line[2][0])
				line[2][1]=int(line[2][1].strip())
			if not line[3]=="":line[3]=int(line[3])#radius
			if not line[4]=="":
				line[4]= line[4].strip("()")
				line[4]= line[4].strip("[]")
				line[4]= line[4].split(",")
				line[4][0]=int(line[4][0])
				line[4][1]=int(line[4][1].strip())
			if not line[5]=="":line[5]=float(line[5])#Ref_Angle
			if not line[7]=="":line[7]=float(line[7])#North_Angle
			if not line[8]=="":line[8]=float(line[8])#CalcNorthAngle			
			if not line[6]=="":North_list.append(line[6])
			if not line[9]=="":Wood_list.append(line[9])
			if not line[10]=="":
				line[10]= line[10].strip("()")
				line[10]= line[10].strip("[]")
				line[10]= line[10].split(",")
				line[10][0]=int(line[10][0])
				line[10][1]=int(line[10][1].strip())
			if not line[11]=="":line[11]=int(line[11])
			# Make Datalists
			Data.append(line)
			files.append(line[0])
			filenames.append(line[1])
		North_list=list(set(North_list))
		Wood_list=list(set(Wood_list))
		North_list.sort()
		Wood_list.sort()
		for i in range(len(North_list)):
			North_liststore.append([North_list[i]])
		for i in range(len(Wood_list)):
			Wood_liststore.append([Wood_list[i]])			
		for i in range(len(allfiles)):
			try:
				x=files.index(allfiles[i])
			except:
				Data.append([allfiles[i],allfilenames[i],"","","","","","","","","",""])
				files.append(allfiles[i])
				files.append(allfilenames[i])
		allfiles=files
		allfilenames=filenames
		center=Data[0][2]
		radius=Data[0][3]
		if not len(center)<2: 
			self.builder.get_object('entryX').set_text(str(center[0]))
			self.builder.get_object('entryY').set_text(str(center[1]))
			self.builder.get_object('entryRadius').set_text(str(radius))
		CurrentImage=""# Prevents from Storing on Image Load
		self.InitializeTreeItems()
		self.loadImage(allfiles[0],allfilenames[0])
		
	def loadData(self,imagename):
		global Data,center,radius,North_Image,North_Angle,Refxy,RefAngle,WoodRef,North_Reference_Point,CalcNorthAngle,allfilenames,Burn_center,Burn_radius
		global North_list,Wood_list
		#print "Loading "+imagename
		n=allfilenames.index(imagename)
		Refxy=Data[n][4]
		RefAngle=Data[n][5]
		CalcNorthAngle=""
		if not Data[n][6]=="":
			North_Image=Data[n][6]
			x=allfilenames.index(North_Image)
			North_Angle=Data[x][7]
			North_Reference_Point=Data[x][4]
			if not Data[n][4]=="":self.calculate_rotations()
			try:
				nl=North_list.index(North_Image)
			except:
				1#print "Initial Northreference Loading"
			else:
				self.builder.get_object("combobox1").set_active(nl)
		if not Data[n][9]=="":
			WoodRef=Data[n][9]	
			try:
				wl=Wood_list.index(WoodRef)
			except:
				1#print "Initial Woodreference Loading"
			else:
				self.builder.get_object("combobox2").set_active(wl)
		if not Data[n][10]=="":
			Burn_center=Data[n][10]	
		else:
			Burn_center=""
		if not Data[n][11]=="":
			Burn_radius=Data[n][11]	
		else:
			Burn_radius=""
		#set Labels
		self.builder.get_object('labelWoodRef').set_label(WoodRef)
		self.builder.get_object('labelRefNorth').set_label(str(North_Image) + ": "+ str(North_Angle))
		if Refxy=="":
			self.builder.get_object('labelRefPoint').set_label("/")
		else:
			self.builder.get_object('labelRefPoint').set_label(str(Refxy[0])+" / "+str(Refxy[1]))
		self.builder.get_object('labelRefAngle').set_label(str(RefAngle))
	
	def loadImage(self,imagepath,imagename):
		global SourceImage,DrawImage,Zoomfactor,RefAngle,Refxy,CurrentImage,North_Angle,CalcNorthAngle
		if not CurrentImage=="":self.storeData()
		self.loadData(imagename)
		CurrentImage=imagename
		DrawImage = Image.open(imagepath)
		DrawImage=DrawImage.convert('RGB')
		SourceImage=DrawImage.copy()
		DrawImage=self.drawCenter(DrawImage)
		Zoomfactor=self.DrawImage(DrawImage)
		self.builder.get_object('labelCurrImage').set_label(imagename)
		if North_Image==CurrentImage:
			DrawImage=self.drawNorth(DrawImage,center,radius,North_Angle)
		else:
			if not CalcNorthAngle=="": DrawImage=self.drawCalcNorth(DrawImage,center,radius,CalcNorthAngle)

		if not RefAngle==[]:
			DrawImage=self.drawRef(DrawImage,center,radius,Refxy)
		else:
			Refxy=[]
			self.builder.get_object('labelRefPoint').set_label("")
			self.builder.get_object('labelRefAngle').set_label("")
		DrawImage=self.drawBurnmask(DrawImage)
		DrawImage=self.drawRef(DrawImage,center,radius,Refxy)
		
		
	def on_buttonNext_clicked	(self, action, *args):
		self.MoveNext()
	
	def MoveNext(self):
		global allfiles, allfilenames
		treeview = self.builder.get_object("treeview1")
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		path = model.get_path(iter)
		if not path[0] >= (len(allfiles)-1):
			path=path[0]+1
		else:
			path=0
		self.loadImage(allfiles[path],allfilenames[path])
		treeselection.select_path(path)
	
	def on_buttonPrev_clicked(self, action, *args):
		self.MovePrevious()
	
	def MovePrevious(self):
		global allfiles, allfilenames
		treeview = self.builder.get_object("treeview1")
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		path = model.get_path(iter)
		if not path[0] ==0:
			path=path[0]-1
		else:
			path=(len(allfiles)-1)
		self.loadImage(allfiles[path],allfilenames[path])
		treeselection.select_path(path)
		
	def on_MainWin_expose_event(self,widget,*user_data):
		global DrawImage
		if not DrawImage==0:
			self.DrawImage(DrawImage)
	
	def DrawImage(self,img):
		width, height=img.size
		pb = self.Image_to_GdkPixbuf (img)
		gim=self.builder.get_object('image1')
		widget=self.builder.get_object('eventbox1')
		allocation = widget.get_allocation()
		dst_width, dst_height = allocation.width, allocation.height
		if dst_width<500:
			dst_width=800
			dst_height=800
		scw=dst_width/(width*1.0)
		sch=dst_height/(height*1.0)		
		if scw<sch:
			w=dst_width
			h=int(height*scw)
			zf=scw
		else:
			w=int(width*sch)
			h=dst_height
			zf=sch
		scaled_buf = pb.scale_simple(w,h,gtk.gdk.INTERP_BILINEAR)
		gim.set_from_pixbuf(scaled_buf)
		return zf

	def Image_to_GdkPixbuf (self,image):
		file = StringIO.StringIO ()
		image.save (file, 'ppm')
		contents = file.getvalue()
		file.close ()
		loader = gtk.gdk.PixbufLoader ('pnm')
		loader.write (contents, len (contents))
		pixbuf = loader.get_pixbuf ()
		loader.close ()
		return pixbuf
	
	def on_toggleCenter_toggled(self, widget, *args):
		global Action
		state=widget.get_active()
		if state == True:
			Action =1
		else:
			Action =0
	
	def on_toggleRadius_toggled(self, widget, *args):
		global Action
		state=widget.get_active()
		if state == True:
			Action =2
		else:
			Action =0
	
	def on_toggleSetNorth_toggled(self, widget, *args):
		global Action
		state=widget.get_active()
		if state == True:
			Action =3
		else:
			Action =0
	
	def on_toggleSetRefPoint_toggled(self, widget, *args):
		global Action
		state=widget.get_active()
		if state == True:
			Action =4
		else:
			Action =0
	
	def on_toggleMask_toggled(self, widget, *args):
		global Action
		state=widget.get_active()
		if state == True:
			Action =5
		else:
			Action =0
	
	def on_buttonSetWood_clicked(self, action, *args):
		global WoodRef
		WoodRef=CurrentImage
		try:
			n=Wood_list.index(CurrentImage)
		except:
			Wood_liststore.append([CurrentImage])
			Wood_list.append(CurrentImage)
			self.builder.get_object("combobox2").set_active(len(Wood_list)-1)
		else:
			self.builder.get_object("combobox2").set_active(n)
		self.builder.get_object('labelWoodRef').set_label(WoodRef)

	def	on_buttonSetManual_clicked (self, action, *args):
		global DrawImage,SourceImage,center,radius,Zoomfactor
		center=(int(self.builder.get_object('entryX').get_text()),int(self.builder.get_object('entryY').get_text()))
		radius=int(self.builder.get_object('entryRadius').get_text())
		DrawImage=SourceImage.copy()
		DrawImage=self.drawCenter(DrawImage)
		if North_Image==CurrentImage: DrawImage=self.drawNorth(DrawImage,center,radius,North_Angle)
		DrawImage=self.drawRef(DrawImage,center,radius,Refxy)
		Zoomfactor=self.DrawImage(DrawImage)
		
		
	def on_eventbox1_button_press_event(self,widget,event,*user_data):
		global center,Burn_center,Zoomfactor
		if Action ==5: #set BurnCenter
			Burn_center=(int(event.x*(1/Zoomfactor))-center[0],int(event.y*(1/Zoomfactor))-center[1])
		return
		
	def on_eventbox1_motion_notify_event(self, widget, event):
		global Action,DrawImage,SourceImage,Zoomfactor,center,radius
		xy=(int(event.x*(1/Zoomfactor)),int(event.y*(1/Zoomfactor)))
		if Action==0: return #do nothing
		if Action==1: #set Center
			center=xy
			self.builder.get_object('entryX').set_text(str(xy[0]))
			self.builder.get_object('entryY').set_text(str(xy[1]))
		if Action ==2: #set Radius
			radius=int(np.sqrt((center[0]-xy[0])*(center[0]-xy[0])+(center[0]-xy[1])*(center[1]-xy[1])))
			self.builder.get_object('entryRadius').set_text(str(radius))
		if Action ==3: #set North
			North_Angle=self.point2angle(xy,center)
			self.builder.get_object('labelRefNorth').set_label(str(round(North_Angle,1)))
		DrawImage=SourceImage.copy()
		DrawImage=self.drawCenter(DrawImage)
		if Action ==3: DrawImage=self.drawNorth(DrawImage,center,radius,North_Angle)
		Zoomfactor=self.DrawImage(DrawImage)
		return
		
	def on_eventbox1_button_release_event(self,widget,event,*user_data):
		global Action,DrawImage,SourceImage,center,radius,Zoomfactor,North_Angle,Refxy,RefAngle,North_Image
		global CurrentImage,North_Reference_Point,CalcNorthAngle,North_list,North_liststore
		global Burn_center,Burn_radius
		xy=(int(event.x*(1/Zoomfactor)),int(event.y*(1/Zoomfactor)))
		if Action==0: return #do nothing
		if Action==1: #set Center
			#print 'Action 1'
			center=xy
			self.builder.get_object('entryX').set_text(str(xy[0]))
			self.builder.get_object('entryY').set_text(str(xy[1]))
			self.builder.get_object('toggleCenter').set_active(False)
		if Action ==2: #set Radius
			#print 'Action 2'
			radius=int(np.sqrt((center[0]-xy[0])*(center[0]-xy[0])+(center[0]-xy[1])*(center[1]-xy[1])))
			self.builder.get_object('entryRadius').set_text(str(radius))
			self.builder.get_object('toggleRadius').set_active(False)
		if Action ==3: #set North
			#print 'Action 3'
			North_Angle=self.point2angle(xy,center)
			North_Image=CurrentImage
			self.builder.get_object('labelRefNorth').set_label(CurrentImage +": "+ str(round(North_Angle,1)))
			try:
				n=North_list.index(CurrentImage)
			except:
				North_liststore.append([CurrentImage])
				North_list.append(CurrentImage)
				self.builder.get_object("combobox1").set_active(len(North_list)-1)
			else:
				self.builder.get_object("combobox1").set_active(n)
			self.builder.get_object('toggleSetNorth').set_active(False)
		if Action==4:#set Reference
			#print 'Action 4'
			Refxy=xy
			RefAngle=self.point2angle(xy,center)
			if North_Image==CurrentImage: North_Reference_Point=xy
			self.builder.get_object('labelRefPoint').set_label(str(Refxy[0])+" / "+str(Refxy[1]))
			self.builder.get_object('labelRefAngle').set_label(str(RefAngle))
			self.calculate_rotations()
			self.builder.get_object('labelRotation').set_label(str(round(CalcNorthAngle,1)))
		DrawImage=SourceImage.copy()
		DrawImage=self.drawCenter(DrawImage)
		if North_Image==CurrentImage:
			DrawImage=self.drawNorth(DrawImage,center,radius,North_Angle)
		else:
			if not CalcNorthAngle=="": DrawImage=self.drawCalcNorth(DrawImage,center,radius,CalcNorthAngle)
		if Action==5:#set Burn_Center
			Burn_radius=int(np.sqrt((center[0]+Burn_center[0]-xy[0])*(center[0]+Burn_center[0]-xy[0])+(center[1]+Burn_center[1]-xy[1])*(center[1]+Burn_center[1]-xy[1])))
			if not Burn_radius==0:
				DrawImage=self.drawBurnmask(DrawImage)
			else:
				Burn_radius=""
				Burn_center=""
		DrawImage=self.drawRef(DrawImage,center,radius,Refxy)
		Zoomfactor=self.DrawImage(DrawImage)
	
	def InitializeTree(self):
		global treestore
		treeview1 = self.builder.get_object("treeview1")
		# add columns:
		C_DATA_COLUMN_NUMBER_IN_MODEL = 0
		cell0 = gtk.CellRendererText()
		#cell1 =gtk.CellRendererToggle()	
		col0 = gtk.TreeViewColumn("Sample", cell0,text=C_DATA_COLUMN_NUMBER_IN_MODEL)
		#col1 = gtk.TreeViewColumn("Complete", cell1)
		#col1.add_attribute(cell1, "active", 1)
		treeview1.append_column(col0)
		#treeview1.append_column(col1)
		#treestore = gtk.ListStore('gchararray','gboolean')
		treeview1.set_model(treestore)
		treeview1.set_reorderable(True)
	
	def InitializeTreeItems(self):
		global treestore,allfilenames
		treestore = gtk.ListStore('gchararray')
		for i in xrange(len(allfilenames)):
			treestore.append([allfilenames[i]])
		treeview1 = self.builder.get_object("treeview1")
		treeselection=treeview1.get_selection()
		treeselection.select_path(0)
		treeview1.set_model(treestore)
		treeview1.set_reorderable(True)
	
	def on_treeview1_cursor_changed(self,treeview, *user_param1):
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		path = model.get_path(iter)
		#self.LoadSet(allscans[path[0]])
		self.loadImage(allfiles[path[0]],allfilenames[path[0]])
	
	def InitializeNorth(self):
		global North_liststore
		combobox1 = self.builder.get_object("combobox1")
		combobox1.set_model(North_liststore)
		#combobox1.set_active(0)
		cell = gtk.CellRendererText()
		combobox1.pack_start(cell, True)
		combobox1.add_attribute(cell, "text", 0)
	
	def on_combobox1_changed (self, combobox):
		global Data,allfilenames,NoethRefImage,North_Angle,North_Angle,North_Reference_Point,North_Image,CurrentImage
		model = combobox.get_model()
		index = combobox.get_active()
		if index:
			if not CurrentImage==North_Image:
				NI=model[index][0]
				North_Image=NI
				n=allfilenames.index(NI)
				North_Angle=Data[n][7]
				try: x=allfilenames.index(Data[n][6])
				except:
					1#
				else:
					North_Reference_Point=Data[x][4]
				self.builder.get_object('labelRefNorth').set_label(NI +": "+ str(round(North_Angle,1)))
				#self.storeData()
				#self.loadData(CurrentImage)
		return	
	
	def InitializeWood(self):
		global Wood_liststore
		combobox2 = self.builder.get_object("combobox2")
		combobox2.set_model(Wood_liststore)
		#combobox2.set_active(0)
		cell = gtk.CellRendererText()
		combobox2.pack_start(cell, True)
		combobox2.add_attribute(cell, "text", 0)
	
	def on_combobox2_changed (self, combobox):
		global WoodRef
		model = combobox.get_model()
		index = combobox.get_active()
		if index:
			WoodRef=model[index][0]
		return
	
	def on_buttonExit_clicked(self, action, *args):
		self.quit()
	
	def drawCenter(self,image):
		global center,radius
		draw = ImageDraw.Draw(image)
		draw.line((center[0]-20,center[1], center[0]+20, center[1]), fill="#ff0000")
		draw.line((center[0],center[1]-20, center[0], center[1]+20), fill="#ff0000")
		draw.ellipse((center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius), outline="#ff0000") #fill=(255, 255, 255)) 
		del draw 
		return image
	
	def drawNorth(self,image,center,radius,North_Angle):
		if not North_Angle=="":
			North_Angle_rad=North_Angle*(np.pi/180)
			if North_Angle>180.0:
				NP=(center[0]+np.sin(North_Angle_rad)*radius,center[1]-np.cos(North_Angle_rad)*radius)
			else:
				NP=(center[0]+np.sin(North_Angle_rad)*radius,center[1]-np.cos(North_Angle_rad)*radius)
			draw = ImageDraw.Draw(image)
			pradius=10
			draw.ellipse((NP[0]-pradius, NP[1]-pradius, NP[0]+pradius, NP[1]+pradius),fill="#0000ff")
			draw.line((center[0],center[1], NP[0], NP[1]), fill="#0000ff")
			del draw 
		return image
		
	def drawCalcNorth(self,image,center,radius,North_Angle):
		if not North_Angle=="":
			North_Angle_rad=North_Angle*(np.pi/180)
			if North_Angle>180.0:
				NP=(center[0]+np.sin(North_Angle_rad)*radius,center[1]-np.cos(North_Angle_rad)*radius)
			else:
				NP=(center[0]+np.sin(North_Angle_rad)*radius,center[1]-np.cos(North_Angle_rad)*radius)
			draw = ImageDraw.Draw(image)
			pradius=10
			draw.ellipse((NP[0]-pradius, NP[1]-pradius, NP[0]+pradius, NP[1]+pradius),fill="#ff0000")
			draw.line((center[0],center[1], NP[0], NP[1]), fill="#ff0000")
			del draw 
		return image
	
	def drawRef(self,image,center,radius,RP):
		global RefAngle,North_Angle,North_AnglePoint
		if not RP=="":
			RefAngle=self.point2angle(RP,center)
			RefAngle_rad=RefAngle*(np.pi/180)
			if RefAngle>180.0:
				NP=(center[0]+np.sin(RefAngle_rad)*radius,center[1]-np.cos(RefAngle_rad)*radius)
			else:
				NP=(center[0]+np.sin(RefAngle_rad)*radius,center[1]-np.cos(RefAngle_rad)*radius)
			draw = ImageDraw.Draw(image)
			pradius=10
			draw.ellipse((RP[0]-pradius, RP[1]-pradius, RP[0]+pradius, RP[1]+pradius),fill="#00ff00")
			draw.line((center[0],center[1], NP[0], NP[1]), fill="#00ff00")
			del draw 
		return image
		
	def drawBurnmask(self,image): #Oct2011 Added Sunmasks
		global Burn_center,Burn_radius
		if not Burn_radius =="":
			draw = ImageDraw.Draw(image)
			draw.ellipse((center[0]+Burn_center[0]-Burn_radius, center[1]+Burn_center[1]-Burn_radius,center[0]+ Burn_center[0]+Burn_radius, center[1]+Burn_center[1]+Burn_radius),fill="#ffd700")
			del draw 
		return image
	
	def calculate_rotations(self):
		global Refxy,center,North_Reference_Point,North_Angle,CalcNorthAngle,North_Reference_Angle
		RefAngle=self.point2angle(Refxy,center)
		North_Reference_Angle=self.point2angle(North_Reference_Point,center)
		CalcNorthAngle=(RefAngle)-(North_Reference_Angle-North_Angle)
		if CalcNorthAngle<0:
				CalcNorthAngle=CalcNorthAngle+360
		if CalcNorthAngle>=360:
				CalcNorthAngle=CalcNorthAngle-360
		#print "North:"+str(CalcNorthAngle)
	
	def point2angle(self,xy,center):
		x=1.0*xy[0]-center[0]
		y=-(1.0*xy[1]-center[1])
		if y==0 and x>0:
			angle=90.0
		elif y==0 and x<0:
			angle=270.0
		else: 
			angle=np.arctan(x/y)*(180/np.pi)
			if x>0:
				if y<0:
					angle=angle+180
			else:
				if y<0:
					angle=angle+180
				else:
					angle=angle+360
		#print x,y,angle
		return angle	

if __name__ == '__main__':
	app = ImgRot()
	app.run()


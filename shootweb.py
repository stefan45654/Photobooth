#!/usr/bin/pythonRoot
from __future__ import division
from PIL import Image
from PIL import ImageFilter
from PIL import ImageFont
from PIL import ImageDraw
from flup.server.fcgi import WSGIServer
from subprocess import call
from multiprocessing import Process,Pipe
from configobj import ConfigObj
import cgitb
import  time
import RPi.GPIO as GPIO
import sys, urlparse
import os
import string
import subprocess
import commands
import datetime


cgitb.enable()

button= 8

#GPIO.setmode(GPIO.BOARD)
#GPIO.setwarnings(False)

def log(text):
	lg = open('/var/www/log/log.txt','a+')
	if text != '!':
		now = datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")	
		lg.write(now+' '+text+'\n')
	else:
		lg.write('\n')
	lg.close

def sendmail(to):
	log('sending collagemail to '+to)
	call(['mpack','-s','Photobooth Lydia und Stephan','-d','/var/www/description.txt','/var/www/collage/collage.jpg',to])	 

def collage():
	
	#load the white background
	log('Loading Background')
	back= Image.open("/var/www/back-names.jpg")
	width_back = back.size[0]
	height_back = back.size[1]
	back_resolution = int(width_back / 148) # calculate back resolution in pixel/mm
	
	offset_bp = 2 #offset zwischen den bildern in mm
	offset_l = 20 #offset von links (senkrechter Streifen) in mm
	
	offset_bp_pix = offset_bp * back_resolution
	offset_l_pix = offset_l * back_resolution
	im_insertheight = int((height_back -(3*offset_bp_pix))/2)
	im_insertwidth = int((width_back -(2*offset_bp_pix) -(offset_l_pix))/2)
	
	#get list of all photos on the camera
	image_string = commands.getstatusoutput('ls -t /var/www/current/')
	image_list = image_string[1].split('\n')
	
	#get list of all previous collages
	collage_string = commands.getstatusoutput('ls -t /var/www/archive/')
	collage_list = collage_string[1].split('\n')
	#calculate current collage number
	num = str(int(len(collage_list)/2))
	imgnum = len(image_list)
	log('there are '+str(imgnum)+' pictures in the folder')
	log('there are '+str(num)+' collages in the archive')
	if imgnum == 4:  #proceed if there are four pictures in the folder
		call(['mkdir','/var/www/archive/collage'+num+'/'])
		#create a directory in the archive
		#load the images and assemble them
		img_list_fullpath=create_imglist(image_list)
		par1,chi1 = Pipe()
		par2,chi2 = Pipe()
		par3,chi3 = Pipe()
		par4,chi4 = Pipe()
		
		p1 = Process(target=resize,args=(chi1,im_insertheight,im_insertwidth,img_list_fullpath[0],))
		p2 = Process(target=resize,args=(chi2,im_insertheight,im_insertwidth,img_list_fullpath[1],))
		p3 = Process(target=resize,args=(chi3,im_insertheight,im_insertwidth,img_list_fullpath[2],))
		p4 = Process(target=resize,args=(chi4,im_insertheight,im_insertwidth,img_list_fullpath[3],))
		
		p1.start()
		p2.start()
		p3.start()
		p4.start()
		imgs = [Image]*4
		imgs[0]=par1.recv()
		imgs[1]=par2.recv()
		imgs[2]=par3.recv()
		imgs[3]=par4.recv()
		
		p1.join()
		p2.join()
		p3.join()
		p4.join()
		
		for i in range(0, 4):
			log('Processing Photo '+image_list[i])
			#apply filter to the image
			call(['cp','/var/www/current/'+image_list[i],'/var/www/archive/collage'+num+'/'])			
			#place image on white background
			y = 0
			if i > 1:
				y = y + im_insertheight+offset_bp_pix
			back_box = (offset_bp_pix+i*(im_insertwidth+offset_bp_pix) % ((2*offset_bp_pix)+(2*im_insertwidth)), y + offset_bp_pix,(im_insertwidth+offset_bp_pix)+i*(im_insertwidth+offset_bp_pix) % ((2*offset_bp_pix)+(2*im_insertwidth)), y + (im_insertheight+offset_bp_pix))
			back.paste(imgs[i], back_box)
		#save the collage onto the sd card
		log('Saving final collage')
		back.save('/var/www/archive/collage'+num+'.jpg')
		call(['cp','/var/www/archive/collage'+num+'.jpg','/var/www/collage/collage.jpg'])
	call(['rm','-r','/var/www/current/'])

def create_imglist(pathlist):
	list = ['','','','']
	for i in range(0,4):
		list[i] = '/var/www/current/'+pathlist[i]
	return list
	
def resize(conn,insertheight,insertwidth,path):
	# resize image
	image = Image.open(path)
	width = image.size[0]
	height = image.size[1]
	new_width = int(round(height * (insertwidth/insertheight), 0))
	offset = int(round(((width - new_width) / 2), 0))
	box = (offset, 0, new_width + offset, height)
	image = image.crop(box)
	image = image.resize((insertwidth, insertheight))
	conn.send(image)
	conn.close()

def app(environ, start_response):
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)
	start_response("200 OK", [("Content-Type", "text/html")])
	i = urlparse.parse_qs(environ["QUERY_STRING"])
	yield('&nbsp; ')
	if "q" in i:
		if i["q"][0] == "s":	#shoot the camera 4 times
			cmd='gphoto2 -F 4 -I 2.5 --capture-image-and-download --filename /var/www/current/pic%n.jpg --force-overwrite'
			ps = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=None)
			while True:
				output = ps.stdout.readline()
				if output == '' and ps.poll() is not None:
					break
				if output:
					if output.strip()[17]=='1':
						yield('1')
					if output.strip()[17]=='2':
						yield('2')
					if output.strip()[17]=='3':
						yield('3')
					if output.strip()[17]=='4':
						yield('4')
			yield('done')
			log('shooted 4 fotos')
			log('!')
		
		elif i["q"][0] == "c":
			config = ConfigObj('/var/www/photobooth.config')
			h = []
			h.append(config['header1'])
			h.append(config['header2'])
			yield(h)
            
		elif i["q"][0] == "i": # initialize the camera
			text = commands.getstatusoutput('gphoto2 --auto-detect')
			yield('detected')
			log('camera '+text[1][107:125]+' detected')
			log('!')
            
		elif i["q"][0] == "v": # take a preview image
			commands.getstatusoutput('gphoto2 --capture-preview --force-overwrite')
			time.sleep(0.5)
			yield('captured')
			
		elif i["q"][0] == "w":	#wait for the remote
			log('Waiting for Button Press')
			GPIO.setup(button,GPIO.IN,GPIO.PUD_DOWN)
			GPIO.wait_for_edge(button,GPIO.RISING)
			time.sleep(0.2)
			if GPIO.input(button) == GPIO.HIGH:
				commands.getstatusoutput('gphoto2 --set-config viewfinder=1')
				yield('pressed')
				log('Button pressed')
				log('!')

		elif i["q"][0] == "m": #create the collage
			collage()	#open collage function
			yield('collaged')
			log('!')
            
		elif i["q"][0] == "p": #print the collage
			log('start printing')
			call(['lpr','-s','-o','fit-to-page','-P','Canon_CP910','/var/www/collage/collage.jpg'])
			flg = True
			while flg == True:
				time.sleep(1)
				printer_string = commands.getstatusoutput('lpstat -p Canon_CP910')
				log(printer_string[1][20])
				if printer_string[1][20]=='i':
					flg=False
			yield('printed')
			log('Printing complete')
			log('!')
			
		elif i["q"][0] == 'r':
			commands.getstatusoutput('gphoto2 --set-config viewfinder=0')
			time.sleep(0.5)
			call(['gphoto2','--set-config','viewfinder=0'])
			yield('dropped')
			log('mirror dropped')
			log('!')

if __name__ == '__main__':	
	WSGIServer(app).run()

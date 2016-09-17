#!/usr/bin/pythonRoot
from __future__ import division
from PIL import Image
from PIL import ImageFilter
from PIL import ImageFont
from PIL import ImageDraw,ImageOps
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
import threading

def hex_to_rgb(value): #calculate rgb values from hex color code
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

cgitb.enable()
button_lock = threading.Lock()
button= 8
config = ConfigObj('/var/www/photobooth.config')
coll_section = config['Collage']
txt1=coll_section['text1'][0]
txt1c=hex_to_rgb(coll_section['text1'][1])
txt2=coll_section['text2'][0]
txt2c=hex_to_rgb(coll_section['text2'][1])
#load the white background
w=int(coll_section['width_res'])

offset_bp = float(coll_section['bp_offset']) #offset zwischen den bildern in mm
offset_r = float(coll_section['r_offset']) #offset von links (senkrechter Streifen) in mm
offset_l = float(coll_section['l_offset'])
offset_t = float(coll_section['t_offset'])
size_text1 = float(coll_section['text1_size'])
size_text2 = float(coll_section['text2_size'])
offset_text = float(coll_section['text_offset'])
offset_between_texts = float(coll_section['offset_between_texts'])
txt1_font = coll_section['text1_font']
txt2_font = coll_section['text2_font']

w_mm= int(coll_section['width'])
h_mm= int(coll_section['height'])
h = int(w*h_mm/w_mm)
pix_mm=w/w_mm

offset_bp_pix = int(offset_bp * pix_mm)
offset_left_pix = int(offset_l*pix_mm)
offset_top_pix = int(offset_t*pix_mm)
offset_right_pix = int(offset_r*pix_mm)
size_text1_pix = int(size_text1*pix_mm)
size_text2_pix = int(size_text2*pix_mm)
offset_text_pix = int(offset_text*pix_mm)
offset_between_texts_pix = int(offset_between_texts*pix_mm)
back = Image.new('RGBA',(w,h),(255,255,255,0))

#GPIO.setmode(GPIO.BOARD)
#GPIO.setwarnings(False)

def log(text):	#append the logfile
	lg = open('/var/www/log/log.txt','a+')
	if text != '!':
		now = datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")	
		lg.write(now+' '+text+'\n')
	else:
		lg.write('\n')
	lg.close
	


def sendmail(to): #old function (not used right now)
	log('sending collagemail to '+to)
	call(['mpack','-s','Photobooth Lydia und Stephan','-d','/var/www/description.txt','/var/www/collage/collage.jpg',to])
	
def create_collage_back():

	font1 = ImageFont.truetype(txt1_font,int(size_text1_pix))
	font2 = ImageFont.truetype(txt2_font,int(size_text2_pix))

	txtimg1 = Image.new('L',(h,size_text1_pix))
	txtimg2 = Image.new('L',(h,size_text1_pix))

	draw1 = ImageDraw.Draw(txtimg1)
	draw2 = ImageDraw.Draw(txtimg2)

	w1,h1 = draw1.textsize(txt1,font=font1)
	w2,h2 = draw2.textsize(txt2,font=font2)

	draw1.text((int(h/2)-int(w1/2),int((size_text1_pix-h1)/2)),txt1,font=font1,fill=255)
	draw2.text((int(h/2)-int(w2/2),int((size_text1_pix-h2)/2)),txt2,font=font2,fill=255)

	rot1=txtimg1.rotate(90,expand=1)
	rot2=txtimg2.rotate(90,expand=1)

	back.paste(ImageOps.colorize(rot1,(0,0,0),txt1c),(w-(offset_right_pix - offset_text_pix),0),rot1)
	back.paste(ImageOps.colorize(rot2,(0,0,0),txt2c),(w-(offset_right_pix - offset_between_texts_pix - offset_text_pix - h1),0),rot2)


def collage():	
	im_insertheight = int((h -offset_bp_pix-(2*offset_top_pix))/2)
	im_insertwidth = int((w - offset_bp_pix - offset_right_pix - offset_left_pix)/2)
	
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
		
		for i in range(0,2):
			for j in range(0,2):
				log('Processing Photo '+image_list[j+(i*2)])
				call(['cp','/var/www/current/'+image_list[j+(i*2)],'/var/www/archive/collage'+num+'/'])			
				#place image on white background
				back_box = (offset_left_pix+(j*(im_insertwidth+offset_bp_pix)),offset_top_pix+(i*(im_insertheight+offset_bp_pix)))
				back.paste(imgs[j+(i*2)], back_box)
		#save the collage onto the sd card
		log('Saving final collage')
		back.save('/var/www/archive/collage'+num+'.jpg',"JPEG",dpi=(int(w/w_mm*25.4),int(w/w_mm*25.4)))
		call(['cp','/var/www/archive/collage'+num+'.jpg','/var/www/collage/collage.jpg'])
		status = 'collaged'
	else:
		status = 'error'
	call(['rm','-r','/var/www/current/'])	#create the collage
	return status

def create_imglist(pathlist):
	list = ['','','','']
	for i in range(0,4):
		list[i] = '/var/www/current/'+pathlist[i]
	return list
	
def resize(conn,insertheight,insertwidth,path): #resize image for the collage (needed for parallelisation)
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
	if "q" in i:
		if i["q"][0] == "s":	#shoot the camera 4 times
			config = ConfigObj('/var/www/photobooth.config')
			coll_section = config['Collage']
			timing = coll_section['shoot_timing']
			cmd='gphoto2 -F 4 -I '+timing+' --capture-image-and-download --filename /var/www/current/pic%n.jpg --force-overwrite'
			ps = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=None)
			while True:
				output = ps.stdout.readline()
				if output == '' and ps.poll() is not None:
					break
				if output:
					if output.strip()[17]=='1':
						yield('1')
					elif output.strip()[17]=='2':
						yield('2')
					elif output.strip()[17]=='3':
						yield('3')
					elif output.strip()[17]=='4':
						yield('4')
			yield('done')
			log('shooted 4 fotos')
			log('!')
		
		elif i["q"][0] == "c":		# read the headers from the config file and yield it to the client
			config = ConfigObj('/var/www/photobooth.config')
			disp_section=config['Display']
			h1= disp_section['header1']
			h1s= disp_section['header1size']
			html1='<h3 style="font-size:'+h1s+'px;text-align:center;color:'+h1[1]+'">'+h1[0]+'</h3>'
			h2 = disp_section['header2']
			h2s = disp_section['header2size']
			html2 = '<h3 style="text-align:center;font-size:'+h2s+'px">'
			for i in range(0,int(len(h2)/2)):
				html2 = html2+'<span style="color:'+h2[(i*2)+1]+';">'+h2[i*2]+' </span>'
			html2 = html2+'</h3>'
			yield(html1+html2)
            
		elif i["q"][0] == "i": # check if the camera and the printer are connected
			text_camera = commands.getstatusoutput('gphoto2 --auto-detect')
			text_printer = commands.getstatusoutput('avahi-browse -t _ipp._tcp')
			if text_camera[1][107:len(text_camera[1])] == '':
				yield('camera not connected or turned off - please connect the camera\n')
				log('no camera connected')
			if text_printer[1] == '':
				yield('printer offline or turned off - please connect the printer to wifi network "Photobooth"')
			if (text_camera[1][107:len(text_camera[1])] != '') & (text_printer [1] != ''):
				yield('detected')
				log('camera '+text_camera[1][107:len(text_camera[1])]+' and printer '+text_printer[1]+'detected')
			log('!')
            
		elif i["q"][0] == "v": # take a preview image
			commands.getstatusoutput('gphoto2 --capture-preview --force-overwrite')
			time.sleep(0.5)
			yield('captured')
			
		elif i["q"][0] == "w":	#wait for the remote
			log('Acquire Lock')
			GPIO.setup(button,GPIO.IN,GPIO.PUD_DOWN)
			button_lock.acquire()		#wait_for_button is not thread safe (fixes runtime errors)
			log('Lock acquired waiting for edge')
			channel=GPIO.wait_for_edge(button,GPIO.RISING,timeout=8000)	#timeout is needed to prevent errors
			if channel is None:
				yield('timeout')
				log('remote timeout')
			else:
				time.sleep(0.2)
				if GPIO.input(button) == GPIO.HIGH:
					commands.getstatusoutput('gphoto2 --set-config viewfinder=1')
					yield('pressed')
					log('Button pressed')
					log('!')
			button_lock.release()

		elif i["q"][0] == "m": #create the collage
			status_= collage()	#open collage function
			yield(status_)
			log('!')
            
		elif i["q"][0] == "p": #print the collage
			log('start printing')
			call(['lpr','-s','-o','media=Custom.255x377','-P','Canon_CP910','/var/www/collage/collage.jpg'])
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
			
		elif i["q"][0] == 'r':	#drop the mirror on the camera
			out = commands.getstatusoutput('gphoto2 --set-config viewfinder=0')
			time.sleep(0.5)
			call(['gphoto2','--set-config','viewfinder=0'])
			if out[0] == 0:
				yield('dropped')
			if out[0] == 256:
				yield('no camera found')

			log('mirror dropped')
			log('!')
		

if __name__ == '__main__':
	log('Started WSGI Server')
	create_collage_back()
	log('Collage Background Created')
	WSGIServer(app).run()

# Photobooth
Photobooth for the Raspberry Pi
This project represents a "Photobooth" for the Raspberry Pi (tested on RPi 2) which uses a webserver and any tablet as a display. The software generates a collage out of 4 images which can then be printed directly on a Canon CP910 dye sublimation printer (or any other airprint printer). As the camera every camera supported by the gphoto2 project can be used.

# needed Packages and Installation

1. Install lighttpd  ```apt-get install lighttpd```
2. Install cups ```apt-get install cups```
3. Install gphoto2 using this nice updater and installer <https://github.com/gonzalo/gphoto2-updater>
4. follow the instructions to install python flup and create the pythonRoot copy following this tutorial <http://davstott.me.uk/index.php/2013/03/17/raspberry-pi-controlling-gpio-from-the-web/>
5. setup lighttpd as in the link above except replace /var/www/doStuff.py with /var/www/shootweb.py in the conf file
6. Install PIL ```pip install pillow``` and avahi-utils ``` apt-get install avahi-utils```
7. copy all the files to the /var/www/ directory
8. restart the webserver with ``` service lighttpd restart```
9. Setup cups for remote access like in <http://thismightbehelpful.blogspot.co.at/2008/09/remote-access-to-cups-web-interface.html>
10. Add pi to the lpadmin group so he can add/remove printers ```adduser pi lpadmin```
11. Wire a Switch for the remote between the Pin 2 (5V) and 8 (GPIO14)
12. Connect the camera to the pi via USB
13. Connect the printer to the same network as the pi
14. install your printer using cups (maybe you need to edit the photobooth.conf file to fit your printer)
15. your Photobooth should be up and running if you visit the website on the pi ( 
 

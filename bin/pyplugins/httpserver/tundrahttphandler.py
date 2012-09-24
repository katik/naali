"""
http://localhost:8886/renderimg?posX=0&posY=6&posZ=30&ortX=0&ortY=0&ortZ=0&ortW=1
"""

import sys
import asyncore

#to move the img file to web server dir
import shutil
import os.path

#http get arg parsing
from urlparse import urlparse, parse_qs

sys.path.append('./pyplugins/httpserver') #omg
import asynchttp

import tundra
import config

server = None

renderer = tundra.Renderer()
frame = tundra.Frame()
cament = None
camera = None


class TundraRequestHandler(asynchttp.MyRequestHandler):
    def replycontent(self, f):
        #note: request is in self.path, as e.g. "render/something?x=y"
        cmd = self.path.split('/')[1]
        cmd = cmd.split('?')[0]
        print self.path
        print cmd

        args = parse_qs(urlparse(self.path).query)

        if self.path == '/':
            testpage(f)

        elif cmd == 'renderimg':
            renderimg(f, args)

        elif cmd == 'client':
            client(f)
        

def testpage(f):
    imgurl = take_and_publish_img()

    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
    f.write("<html>\n<title>Hello from %s</title>\n" % "Tundra")
    f.write("<body>\n<h2>This is a reply from %s</h2>\n" % "Tundra")
    f.write('<img src="%s"/>' % imgurl)

def renderimg(f, args):
    camp = cament.placeable

    posX, posY, posZ = [float(args[argname][0]) 
                        for argname in ['posX', 'posY', 'posZ']]
    ortX, ortY, ortZ, ortW = [float(args[argname][0]) 
                        for argname in ['ortX', 'ortY', 'ortZ', 'ortW']]

    print "New cam pos:", posX, posY, posZ
    print "New cam ort:", ortX, ortY, ortZ, ortW
    camp.SetPosition(posX, posY, posZ)
    quat = camp.Orientation()
    quat.set(ortX, ortY, ortZ, ortW)
    camp.SetOrientation(quat)

    imgurl = take_and_publish_img()
    f.write(imgurl)

def client(f):
    clienthtml = open("../../worldwebview/worldwebview.html")
    f.write(clienthtml.read())

def take_and_publish_img():
    shotpath = camera.SaveScreenshot()
    #would be nice and optimal (no copy but just filesystem pointer change)
    #however, the naming system in EC_Camera depends on the previous images (during the same second)
    #still being there -- ARGH!
    #shutil.move(shotpath, config.IMGDIR)
    shutil.copy(shotpath, config.IMGDIR) #could perhaps just use a symlink for the dir instead!
    imgurl = config.IMGURLBASE + os.path.basename(shotpath)
    return imgurl

def init():
    print "FrameRender camera INIT:"
    global cament, camera

    cament = renderer.MainCamera()
    if cament is not None:
        camera = cament.camera
        

def update(deltatime):
    if camera is None:
        init()
    else:
        asyncore.poll()

assert frame.connect("Updated(float)", update)
server = asynchttp.Server('', 8886, TundraRequestHandler)

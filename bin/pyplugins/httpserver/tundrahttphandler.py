"""
http://localhost:8886/renderimg?posX=0&posY=6&posZ=30&ortX=0&ortY=0&ortZ=0&ortW=1
"""

import sys
import asyncore
import time
import math

import PythonQt

#to move the img file to web server dir
import shutil
import os

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

def euler2quat(yaw, pitch, roll):
    yaw = math.radians(yaw)
    pitch = math.radians(pitch)
    roll = math.radians(roll)
    c1 = math.cos(yaw/2)
    c2 = math.cos(pitch/2)
    c3 = math.cos(roll/2)
    s1 = math.sin(yaw/2)
    s2 = math.sin(pitch/2)
    s3 = math.sin(roll/2)
    c1c2 = c1*c2;
    s1s2 = s1*s2;
    return (c1c2*s3 + s1s2*c3, s1*c2*c3 + c1*s2*s3, c1*s2*c3 - s1*c2*s3, c1c2*c3 - s1s2*s3)
		

filenames = ('nx.png', 'px.png', 'ny.png', 'py.png', 'pz.png', 'nz.png')
dirs = (euler2quat(0, 0, 0),
        euler2quat(180, 0, 0),
        euler2quat(90, 0, 270),
        euler2quat(90, 0, 90),
        euler2quat(90, 0, 0),
        euler2quat(270, 0, 0))

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

        elif cmd == 'cubeimg':
            cubeimg(f, args)

        elif cmd == 'client':
            client(f)

        elif cmd == 'panorama':
            panorama(f)

        elif cmd == 'preview':
            preview(f, args)
            

def testpage(f):
    baseurl = take_and_publish_imgs(512)

    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
    f.write("<html>\n<title>Hello from %s</title>\n" % "Tundra")
    f.write("<body>\n<h2>This is a reply from %s</h2>\n<h3>Cube images</h3>" % "Tundra")
    for name in filenames:
        f.write('<img src="%s"/><br><br>' % (baseurl + name))

    f.write("\n</body></html>")


def preview(f, args):
    index = 0
    camp = cament.placeable
    while True:
        pointname = "p" + str(index)
        if pointname not in args:
            break
        point = args[pointname][0]

        posX, posY, posZ = [float(x) for x in point.split(',')] 
        print "New cam pos: %s" % ([posX, posY, posZ],)

        camp.SetPosition(posX, posY, posZ)

        print 'getting preview for point %s' % point
        take_and_publish_imgs(64, point)
        index += 1



def cubeimg(f, args):
    now = time.time()
    camp = cament.placeable

    posX, posY, posZ = [float(args[argname][0]) for argname in ['posX', 'posY', 'posZ']]

    print "New cam pos:", posX, posY, posZ
    camp.SetPosition(posX, posY, posZ)

    size = int(args['res'][0])
    imgurl = take_and_publish_imgs(size)
    f.write(imgurl)
    print "Taking images took", time.time() - now, "seconds."


def take_and_publish_img():
    shotpath = camera.SaveScreenshot(False)
    #would be nice and optimal (no copy but just filesystem pointer change)
    #however, the naming system in EC_Camera depends on the previous images (during the same second)
    #still being there -- ARGH!
    #shutil.move(shotpath, config.IMGDIR)
    shutil.copy(shotpath, config.IMGDIR) #could perhaps just use a symlink for the dir instead!
    imgurl = config.IMGURLBASE + os.path.basename(shotpath)
    return imgurl

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

def panorama(f):
    panohtml = open("../../worldwebview/worldpanoramaview.html")
    f.write(panohtml.read())

def take_and_publish_imgs(size, path=None):
    now = str(time.time())

    if path is not None:
        picpath = os.path.join(config.IMGDIR, path)
    else:
        picpath = os.path.join(config.IMGDIR, now)
        
    if not os.path.exists(picpath):
        os.mkdir(picpath)
    
    camp = cament.placeable
    origOrientation = camp.Orientation()

    for name, d in zip(filenames, dirs):
        quat = camp.Orientation()
        quat.set(d[0], d[1], d[2], d[3])
        camp.SetOrientation(quat)
        shotpath = camera.GetImageFromScene(PythonQt.Qt.QSize(size, size), "JPEG")
        shutil.move(shotpath, os.path.join(picpath, name))
        
    camp.SetOrientation(origOrientation)
    return config.IMGURLBASE + '/' + now + '/'


def init():
    print "FrameRender camera INIT:"
    global cament, camera
    

    cament = renderer.MainCamera()
    if cament is not None:
        camera = cament.camera
        camera.aspectRatio = 1.0
        camera.verticalFov = 90
        
        
def update(deltatime):
    if camera is None:
        init()
    else:
        asyncore.poll()
assert frame.connect("Updated(float)", update)
server = asynchttp.Server('', 8886, TundraRequestHandler)




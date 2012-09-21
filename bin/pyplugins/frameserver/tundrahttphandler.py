import sys
import asyncore

sys.path.append('./pyplugins/frameserver') #omg
import asynchttp

import tundra

server = None

renderer = tundra.Renderer()
frame = tundra.Frame()
camera = None

class TundraRequestHandler(asynchttp.MyRequestHandler):
    def replycontent(self, f):
        #note: request is in self.path, as e.g. "render/something?x=y"
        shotpath = camera.SaveScreenshot()

        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Hello from %s</title>\n" % "Tundra")
        f.write("<body>\n<h2>This is reply from %s</h2>\n" % self)
        f.write("<p>Screenshot was shot to: %s</p>\n" % shotpath)

def init():
    print "FrameRender camera INIT:"
    global camera

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

from flask import (Flask,
                   Blueprint,
                   Response)
from nokkhum.streaming.camera import Camera
from .. import models


cameras = dict()

module = Blueprint('camera_live', __name__, url_prefix='/cameras')


@module.route('/')
def index():
    return 'Cameras Lives API'


def gen(camera_id):
    """Video streaming generator function."""
    while True:
        frame = cameras[camera_id].get_frame()
        if frame is None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@module.route('/<camera_id>/live', methods=['GET'])
def camera_live(camera_id):
    camera = models.Camera.objects.get(id=camera_id)
    # source = 0
    print('hello live camera')
    if camera_id not in cameras:
        print('first time')
        # source = camera.uri
        cam = Camera()
        cam.set_video_source(camera.uri)
        cam.running = True
        cameras[camera_id] = cam
        cam.start()
    else:
        cam = cameras[camera_id]
        if cam.thread is None:
            cam = Camera()
            cam.set_video_source(camera.uri)
            cam.running = True
            cameras[camera_id] = cam
            cam.start()

    if cameras[camera_id].video_source != camera.uri:
        print('chang uri')
        cam = cameras[camera_id]
        cam.running = False
        cameras.pop(camera_id)
        
        cam = Camera()
        cam.set_video_source(camera.uri)
        cam.running = True
        cameras[camera_id] = cam
        cam.start()
    
    # cam = cameras[camera_id]
    return Response(gen(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   request,
                   )
import json
from flask_login import login_required, current_user
from nokkhum import models
module = Blueprint('maps', __name__, url_prefix='/maps')


@module.route('/', methods=['GET'])
@login_required
def index():
    return 'map'

@module.route('/view', methods=['GET'])
@login_required
def view():
    project_id = request.args.get('project_id')
    zoom = 10
    # if project_id:
        # return project_id
    lon_lat = list()
    data = dict()
    center = list()
    project = models.Project.objects.get(id=project_id)
    for camera in project.cameras:
        # detected_plate = models.DetectedLicensePlate.objects(camera=camera).order_by('-id').first()
        if camera.location[0] == 0 and camera.location[1] == 0:
            continue
        if len(center) == 0:
            center.append(camera.location[0])
            center.append(camera.location[1])
        coord = []
        data = {
                'locations': [],
                'name': '',
                'image_path': ''
                }
        coord.append(camera.location[0])
        coord.append(camera.location[1])
        data['locations'] = coord
        data['name'] = camera.name
        data['image_path'] = camera.get_streaming_url()
        # if detected_plate:
        #     data['image_path'] = detected_plate.image_path
        lon_lat.append(data)

    if len(center) == 0:
        center = [100.523186, 13.736717]
        zoom = 8
    return render_template('/map/index.html',
                           zoom=zoom,
                           center=center,
                           lon_lat=json.dumps(lon_lat))


@module.route('/search', methods=['GET'])
@login_required
def search():
    center = [100.523186, 13.736717]
    zoom = 10
    number = request.args.get('number')
    province = request.args.get('province')
    detected_lp = models.DetectedLicensePlate.objects().order_by('-id')
    data = list()
    cameras = list()

    for lp in detected_lp:
        if lp.number != number:
            continue
        if lp.province != province:
            continue
        if lp.camera in cameras:
            continue
        center =  [lp.camera.location[0], lp.camera.location[1]]
        lp_data = dict()
        lp_data['camera_id'] = str(lp.camera.id)
        lp_data['camera_name'] = lp.camera.name
        lp_data['detected_date'] = lp.detected_date.strftime("%m/%d/%Y, %H:%M:%S")
        lp_data['locations'] = [lp.camera.location[0], lp.camera.location[1]]
        lp_data['image_path'] = lp.image_path
        data.append(lp_data)
        cameras.append(lp.camera)

    return render_template('/map/search.html',
                           zoom=zoom,
                           center=center,
                           data=json.dumps(data))

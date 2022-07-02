from flask_restx import Namespace, Resource
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from santhings import models
from santhings.models import influx
import json
import datetime
from .sensors import get_sensors_data

api = Namespace("videos", description="videos", base_url="/videos")


@api.route("")
class Device(Resource):
    def get(self):
        return '{"data":"get device"}'

    @jwt_required()
    def post(self):
        result = {}
        return jsonify(result)

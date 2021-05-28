from flask_restx import Api

# from flask_marshmallow import Marshmallow
# from flask_jwt_extended import JWTManager

from flask import Blueprint, abort, jsonify

from . import videos

# from . import auth
# from . import devices
from flask_cors import CORS

# from nokkhum import models

# from nokkhum.web.caches import cache


# @cache.memoize(3600)
# def get_service(identity):
#     service = models.Service.objects.with_id(identity)
#     return service


def init_api(app):
    blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config["JWT_SECRET_KEY"] = app.secret_key
    api = Api(
        blueprint,
        title="Nokkhum API System",
        version="1",
        description="API for Surveillance System",
        doc="/doc",
    )

    # Marshmallow(app)
    # jwt = JWTManager(app)
    # jwt._set_error_handler_callbacks(sensors.api)
    # api.add_namespace(auth.api, path="/oauth")
    # api.add_namespace(sensors.api, path="/sensors")
    # api.add_namespace(devices.api, path="/devices")
    api.add_namespace(videos.api, path="/videos")

    app.register_blueprint(blueprint)

    # @jwt.additional_claims_loader
    # def add_claims_to_access_token(service):
    #     data = dict(service=str(service.project.id))
    #     return data

    # @jwt.user_identity_loader
    # def user_identity_lookup(service):
    #     return str(service.id)

    # @jwt.user_lookup_loader
    # def user_loader_callback(jwt_header, jwt_payload):
    #     # print(jwt_header, jwt_payload)
    #     identity = jwt_payload["sub"]
    #     try:
    #         service = get_service(identity)
    #     except Exception as e:
    #         print(e)
    #         errors = [
    #             {
    #                 "status": "403",
    #                 "title": "The service might not have the necessary permissions for a resource",
    #                 "detail": "The service might not have the necessary permissions for a resource",
    #             }
    #         ]

    #         response_dict = dict(errors=errors)
    #         response = jsonify(response_dict)
    #         response.status_code = 403
    #         abort(response)

    #     # print('user jwt', user)
    #     return service

    # return api

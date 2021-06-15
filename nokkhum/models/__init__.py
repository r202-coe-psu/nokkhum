from .users import User
from .oauth2 import OAuth2Token
from .projects import Project
from .cameras import Camera, MotionProperty, CameraBrand, CameraModel
from .compute_nodes import (
    MachineSpecification,
    CPUUsage,
    MemoryUsage,
    DiskUsage,
    SystemLoad,
    ResourceUsage,
    ComputeNode,
)
from .processors import (
    Processor,
    ProcessorReport,
    ProcessorCommand,
    FailRunningProcessor,
)
from .gridviews import GridView
from .storages import StorageShare

__all__ = [
    "User",
    "Project",
    "Camera",
    "MachineSpecification",
    "CPUUsage",
    "MemoryUsage",
    "DiskUsage",
    "SystemLoad",
    "ResourceUsage",
    "ComputeNode",
    "Processor",
    "ProcessorReport",
    "ProcessorCommand",
    "FailRunningProcessor",
    "CameraBrand",
    "CameraModel",
    "GridView",
    "MotionProperty",
    "StorageShare",
    "CameraBrand",
    "CameraModel",
]


from flask_mongoengine import MongoEngine

db = MongoEngine()


def init_db(app):
    db.init_app(app)


def init_mongoengine(settings):
    import mongoengine as me

    dbname = settings.get("MONGODB_DB")
    host = settings.get("MONGODB_HOST", "localhost")
    port = int(settings.get("MONGODB_PORT", "27017"))
    username = settings.get("MONGODB_USERNAME", "")
    password = settings.get("MONGODB_PASSWORD", "")

    me.connect(db=dbname, host=host, port=port, username=username, password=password)

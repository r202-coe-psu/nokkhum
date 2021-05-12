# Database Section
MONGODB_DB = "nokkhumdb"

APP_TITLE = "Nokkhum"

# compute config
NOKKHUM_COMPUTE_INTERFACE = "eth0"

# processor config
NOKKHUM_PROCESSOR_CMD = "nokkhum-processor"
NOKKHUM_PROCESSOR_RECORDER_PATH = "/tmp/nokkhum"
NOKKHUM_PROCESSOR_LOG_PATH = "/tmp/nokkhum"
NOKKHUM_PROCESSOR_ACQUISITOR_DEFAULT_FPS = 10
NOKKHUM_PROCESSOR_ACQUISITOR_DEFAULT_SIZE = (640, 480)

# message config
NOKKHUM_MESSAGE_NATS_HOST = "localhost:4222"
NOKKHUM_STAN_CLUSTER = "nokkhum-stan-cluster"

# steaming config
NOKKHUM_STREAMING_URL = "http://localhost:8081"

# websocket config
# NOKKHUM_WS_URL = 'ws://localhost:8082'

# system login
NOKKHUM_LOGGIN_SYSTEMS = ["ENGPSU"]

# 0.00-24.00 format

DAIRY_TIME_TO_REMOVE = "1:0"
DUE_DATE = 1

NOKKHUM_STREAMING_MAX_WORKER = 2

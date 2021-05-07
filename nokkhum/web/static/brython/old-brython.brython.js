__BRYTHON__.use_VFS = true;
var scripts = {"$timestamp": 1598852341831, "processors.status": [".py", "from browser import ajax,document,window,timer,html\nimport javascript\n\n\nclass ProcessorStatus:\n def __init__(self,url):\n  self.get_state_url=url\n  \n def update_state(self,req_data):\n  for data in req_data:\n  \n  \n   data_id=data[\"camera_id\"]+\"/\"+data[\"project_id\"]\n   i=html.I()\n   \n   if data[\"state\"]in [\"running\",\"start\"]:\n    i.class_name=\"ui green circle icon big\"\n    s=html.SPAN(style={\"color\":\"green\"})\n   elif data[\"state\"]in [\"starting\"]:\n    i.class_name=\"ui yellow circle icon big\"\n    s=html.SPAN(style={\"color\":\"yellow\"})\n   elif data[\"state\"]in [\"stop\"]:\n    i.class_name=\"ui grey circle icon big\"\n    s=html.SPAN(style={\"color\":\"grey\"})\n   elif data[\"state\"]in [\"stopping\"]:\n    i.class_name=\"ui red circle icon big\"\n    s=html.SPAN(style={\"color\":\"red\"})\n    \n   document[f\"state-{data['camera_id']}\"].text=\"\"\n   document[f\"state-{data['camera_id']}\"]<=i+s\n   \n def on_ajax_complete(self,request):\n  request_data=javascript.JSON.parse(request.text)\n  \n  self.update_state(request_data)\n  \n def get_all_camera_state(self):\n  ajax.get(\n  f\"{self.get_state_url}\",oncomplete=self.on_ajax_complete,\n  )\n  \n def start(self):\n  self.get_all_camera_state()\n  timer.set_interval(self.get_all_camera_state,5000)\n", ["browser", "javascript"]], "processors": [".py", "from . import status\n\n__all__=[\"status\"]\n", ["processors", "processors.status"], 1]}
__BRYTHON__.update_VFS(scripts)

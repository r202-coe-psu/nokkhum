__BRYTHON__.use_VFS = true;
var scripts = {"$timestamp": 1604651398460, "processor": [".py", "from browser import (document,\ntimer,\najax,\nhtml)\nimport javascript as js\n\n\n\n\nclass ProcessorController:\n def __init__(self):\n  self._timer=None\n  \n def on_complete(self,req):\n \n  datas=js.JSON.parse(req.text)\n  for data in datas:\n  \n  \n   i=html.I()\n   data_id=data['camera_id']+'/'+data['project_id']\n   if data['state']in ['running','start']:\n    i.class_name=\"ui green circle icon big\"\n    s=html.SPAN(style={'color':'green'})\n    self.disable_button(document.select('.startlpr'),data_id)\n    self.enable_button(document.select('.stoplpr'),data_id)\n   elif data['state']in ['starting']:\n    i.class_name=\"ui yellow circle icon big\"\n    s=html.SPAN(style={'color':'yellow'})\n    self.disable_button(document.select('.stoplpr'),data_id)\n    self.enable_button(document.select('.startlpr'),data_id)\n   elif data['state']in ['stop']:\n    i.class_name=\"ui grey circle icon big\"\n    s=html.SPAN(style={'color':'grey'})\n    self.disable_button(document.select('.stoplpr'),data_id)\n    self.enable_button(document.select('.startlpr'),data_id)\n   elif data['state']in ['stopping']:\n    i.class_name=\"ui red circle icon big\"\n    s=html.SPAN(style={'color':'red'})\n    self.disable_button(document.select('.stoplpr'),data_id)\n    self.enable_button(document.select('.startlpr'),data_id)\n   s <=data['state'].capitalize()\n   document[f\"state-{data['camera_id']}\"].text=''\n   document[f\"state-{data['camera_id']}\"]<=i+s\n   \n def disable_button(self,docs,cam_id):\n  for doc in docs:\n   if doc.id ==cam_id:\n    doc.disabled=True\n    \n def enable_button(self,docs,cam_id):\n  for doc in docs:\n   if doc.id ==cam_id:\n    doc.disabled=False\n    \n def get_data(self):\n \n \n  ajax.get(f'/processor/{self.project_id}/state',\n  oncomplete=self.on_complete,\n  timeout=5)\n  \n  \n  \n def start_timer(self):\n  self.project_id=document['project-id'].value\n  del document['project-id']\n  state.get_data()\n  if self._timer is None :\n   self._timer=timer.set_interval(self.get_data,2000)\n   \n   \nstate=ProcessorController()\nstate.start_timer()\n", ["browser", "javascript"]], "controller": [".py", "from browser import document,ajax,bind\n\n\n@bind(\"button.stoplpr\",\"click\")\ndef stop_lpr(ev):\n\n camera_id,project_id=(ev.target.id).split(\"/\")\n ajax.post(f'/cameras/{camera_id}/stoplpr',\n data={'project_id':project_id})\n \n \n@bind(\"button.startlpr\",\"click\")\ndef start_lpr(ev):\n\n camera_id,project_id=(ev.target.id).split(\"/\")\n ajax.post(f'/cameras/{camera_id}/startlpr',\n data={'project_id':project_id})\n \n \n \n \n \n \n \n", ["browser"]], "resource_usage": [".py", "from browser import document,ajax\n\nfrom browser import timer\nimport javascript as js\n\ndef send_data_card(f):\n datas=f.read()\n datas=js.JSON.parse(datas)\n for data in datas:\n  card_state=document['state'+data['camera']['id']]\n  card_cpu=document['cpu'+data['camera']['id']]\n  card_memory=document['memory'+data['camera']['id']]\n  card_state.clear()\n  card_cpu.clear()\n  card_memory.clear()\n  card_state <='Processor State : '+data['state'].capitalize()\n  if data['state']=='running':\n   card_cpu <='CPU: '+data['cpu']+' %'\n   card_memory <='Memory: '+data['memory']+' MB'\n   \n   \n   \n   \ndef request_url():\n ajax.get('/processor/resource_usage',oncomplete=send_data_card)\n \n \najax.get('/processor/resource_usage',oncomplete=send_data_card)\n_timer=None\n_timer=timer.set_interval(request_url,5000)\n", ["browser", "javascript"]], "camera_selected": [".py", "from browser import (document,\ntimer,\nwebsocket)\nimport javascript as js\n\nfrom browser.html import TR,TD\n\nws_list=[]\nMAXTABLEROW=20\nWS_URL='ws://127.0.0.1:8082'\n\n\ndef send_data(doc,data):\n date=js.Date.new(data['date'])\n tr=doc.get(selector=\"tr\")\n tr_data=TR(TD(data['number'])+\n TD(data['province'])+\n TD(f'{date.toString()}')+\n TD('<img onclick=\"modal_picture(\\'{}\\')\" src=\"{}\" width=\"120\">'.format(data['image-path'],\n data['image-path']))\n )\n ntr=tr_data\n if data['mark']=='black':\n  ntr.className='red'\n elif data['mark']=='white':\n  ntr.className='green'\n if len(tr)>0:\n  doc.insertBefore(ntr,tr[0])\n elif len(tr)==0:\n  doc <=tr_data\n if len(tr)==MAXTABLEROW:\n  doc.removeChild(tr[-1])\n  \n  \ndef on_message(evt):\n data=js.JSON.parse(evt.data)\n \n \n document['platelabel-number-{}'.format(data['camera_id'])].text=data['number']\n \n document['platelabel-province-{}'.format(data['camera_id'])].text=data['province']\n date=js.Date.new(data['date'])\n document['time-{}'.format(data['camera_id'])].text=f'{date.toString()}'\n \n \n \n \n \ndef on_open(evt):\n\n print('opened')\n \n \ndef on_error(evt):\n print('error',evt.data)\n \n \ndef on_close(evt):\n timer.set_timeout(connect,5000)\n \n print('reconnecting')\n \n \ndef ws_bind(ws):\n ws.bind('open',on_open)\n ws.bind('message',on_message)\n ws.bind('error',on_error)\n ws.bind('close',on_close)\n \n \ndef connect(ws_url=None ):\n global WS_URL\n if ws_url:\n  WS_URL=ws_url\n project_id=document.select('.lp-viewer')[0].id\n ws=websocket.WebSocket(WS_URL+'/projects/'+project_id)\n ws_bind(ws)\n \n \nws_url=document['streaming-url'].value\ndel document['streaming-url']\nconnect(ws_url)\n", ["browser", "browser.html", "javascript"]], "camera": [".py", "from browser import (document,\ntimer,\nwebsocket)\nimport javascript as js\n\nfrom browser.html import TR,TD\n\nMAXTABLEROW=20\nWS_URL='ws://127.0.0.1:8082'\n\ndef show_datetime(date):\n def get_month(month_num):\n  print(month_num)\n  month=[\"Jan\",\"Feb\",\"Mar\",\"Apr\",\"May\",\"Jun\",\"Jul\",\"Aug\",\"Sep\",\"Oct\",\"Nov\",\"Dec\"]\n  return month[month_num]\n def add_zero(time_num):\n  if (time_num <10):\n   time_num=str(time_num)\n   time_num=\"0\"+time_num\n  return time_num\n  \n return f'{add_zero(date.getDate())}-{get_month(date.getMonth())}-{date.getFullYear()} {add_zero(date.getHours())}:{add_zero(date.getMinutes())}'\n \n \ndef send_data(doc,data):\n date=js.Date.new(data['date'])\n tr=doc.get(selector=\"tr\")\n tr_data=TR(TD(data['number'])+\n TD(data['province'])+\n TD(show_datetime(date))+\n TD('<img onclick=\"modal_picture(\\'{}\\')\" src=\"{}\" width=\"120\">'.format(data['image-path'],\n data['image-path']))\n )\n ntr=tr_data\n if data['mark']=='black':\n  ntr.className='red'\n elif data['mark']=='white':\n  ntr.className='green'\n if len(tr)>0:\n  doc.insertBefore(ntr,tr[0])\n elif len(tr)==0:\n  doc <=tr_data\n if len(tr)==MAXTABLEROW:\n  doc.removeChild(tr[-1])\n  \n  \ndef on_message(evt):\n data=js.JSON.parse(evt.data)\n \n \n document['platelabel-number'].text=data['number']\n \n document['platelabel-province'].text=data['province']\n date=js.Date.new(data['date'])\n document['time'].text=show_datetime(date)\n \n tabledata=document[\"tabledata\"]\n send_data(tabledata,data)\n \n \ndef on_open(evt):\n\n print('opened')\n \n \ndef on_error(evt):\n print('error',evt.data)\n \n \ndef on_close(evt):\n timer.set_timeout(connect,5000)\n \n print('reconnecting')\n \n \ndef ws_bind(ws):\n ws.bind('open',on_open)\n ws.bind('message',on_message)\n ws.bind('error',on_error)\n ws.bind('close',on_close)\n \n \ndef connect(ws_url=None ):\n global WS_URL\n if ws_url:\n  WS_URL=ws_url\n print('WS_URL',WS_URL)\n camera_id=document.select('.get-id')[0].id\n \n ws=websocket.WebSocket(WS_URL+'/cameras/'+camera_id)\n ws_bind(ws)\n \n \nws_url=document['streaming-url'].value\ndel document['streaming-url']\nconnect(ws_url)\n", ["browser", "browser.html", "javascript"]], "gridviews": [".py", "from . import controllers\n\n__all__=[\"controllers\"]\n", ["gridviews", "gridviews.controllers"], 1], "gridviews.controllers": [".py", "from browser import document,html,ajax\nfrom javascript import JSON\n\n\nclass GridViewController:\n def __init__(self,num_grids=\"4\",save_gird_url=\"\",get_grid_url=\"\"):\n  self.num_grids=num_grids\n  self.save_gird_url=save_gird_url\n  self.get_grid_url=get_grid_url\n  \n def mouseover(self,ev):\n  ev.target.style.cursor=\"pointer\"\n  \n def dragstart_img(self,ev):\n  data=ev.target.id[4:]\n  print(data)\n  ev.dataTransfer.setData(\"text\",data)\n  ev.dataTransfer.effectAllowed=\"move\"\n  \n def dragstart(self,ev):\n  ev.dataTransfer.setData(\"text\",ev.target.id)\n  ev.dataTransfer.effectAllowed=\"move\"\n  \n def dragover(self,ev):\n  ev.dataTransfer.dropEffect=\"move\"\n  ev.preventDefault()\n  \n def drop(self,ev):\n  ''\n\n\n  \n  \n  src=ev.dataTransfer.getData(\"text\")\n  print(src)\n  camera=document[src]\n  camera_id,url=src.split(\"-\")\n  display=document[ev.target.id]\n  try :\n   document[f\"img-{src}\"].unbind(\"dragstart\")\n   del document[f\"img-{src}\"]\n   \n  except Exception as e:\n   pass\n  img=html.IMG(id=f\"img-{src}\",src=url,height=\"100%\")\n  display.clear()\n  display <=img\n  img.draggable=True\n  img.bind(\"dragstart\",self.dragstart_img)\n  ev.preventDefault()\n  \n def save_grid(self,ev):\n  def on_complete(req):\n   if req.status ==200:\n    print(req.text)\n   else :\n    print(\"error \",req.text)\n    \n  displays=document.select(\".displays\")\n  displays_data={}\n  for display in displays:\n   displays_data[display.id]=display.innerHTML\n   \n  ajax.post(\n  self.save_gird_url,\n  data={\n  \"displays\":JSON.stringify(displays_data),\n  \"num_grids\":self.num_grids,\n  },\n  oncomplete=on_complete,\n  headers={\"Content-Type\":\"application/x-www-form-urlencoded\"},\n  )\n  \n def initial_grid(self,req):\n  displays_data=JSON.parse(req.text)\n  for id,img_html in displays_data.items():\n   if not img_html:\n    continue\n   print(img_html)\n   document[id].clear()\n   document[id].innerHTML=img_html\n   for child in document[id].children:\n    child.bind(\"dragstart\",self.dragstart_img)\n    \n def start(self):\n  print(\"start\")\n  for camera in document.select(\".cameras\"):\n   camera.bind(\"mouseover\",self.mouseover)\n   camera.bind(\"dragstart\",self.dragstart)\n   \n  for display in document.select(\".displays\"):\n   display.bind(\"dragover\",self.dragover)\n   display.bind(\"drop\",self.drop)\n   \n  document[\"save-grid\"].bind(\"click\",self.save_grid)\n  \n  ajax.get(\n  f\"{self.get_grid_url}?grid={self.num_grids}\",\n  oncomplete=self.initial_grid,\n  )\n", ["browser", "javascript"]], "processors": [".py", "from . import status\n\n__all__=[\"status\"]\n", ["processors", "processors.status"], 1], "processors.status": [".py", "from browser import ajax,document,window,timer,html,bind\nimport javascript\n\n\nclass ProcessorStatus:\n def __init__(self,url,icon_size=\"large\",type=\"circle\"):\n  self.icon_size=icon_size\n  self.get_state_url=url\n  self.type=type\n  \n def disable_button(self,docs,cam_id):\n  for doc in docs:\n   if doc.id ==cam_id:\n    doc.disabled=True\n    \n def enable_button(self,docs,cam_id):\n  for doc in docs:\n   if doc.id ==cam_id:\n    doc.disabled=False\n    \n @bind(\"button.stoplpr\",\"click\")\n def stop_lpr(ev):\n \n  camera_id,project_id=(ev.target.id).split(\"/\")\n  ajax.post(f\"/cameras/{camera_id}/stoplpr\",data={\"project_id\":project_id})\n  \n @bind(\"button.startlpr\",\"click\")\n def start_lpr(ev):\n \n  camera_id,project_id=(ev.target.id).split(\"/\")\n  ajax.post(f\"/cameras/{camera_id}/startlpr\",data={\"project_id\":project_id})\n  \n def update_state(self,req_data):\n  for data in req_data:\n   print(data)\n   \n   data_id=data[\"camera_id\"]+\"/\"+data[\"project_id\"]\n   i=html.I()\n   color=\"grey\"\n   if data[\"state\"]in [\"running\",\"start\"]:\n    color=\"green\"\n    s=html.SPAN(style={\"color\":\"green\"})\n    self.disable_button(document.select(\".startlpr\"),data_id)\n    self.enable_button(document.select(\".stoplpr\"),data_id)\n   elif data[\"state\"]in [\"starting\"]:\n    color=\"yellow\"\n    s=html.SPAN(style={\"color\":\"yellow\"})\n    self.disable_button(document.select(\".stoplpr\"),data_id)\n    self.enable_button(document.select(\".startlpr\"),data_id)\n   elif data[\"state\"]in [\"stop\"]:\n    color=\"grey\"\n    s=html.SPAN(style={\"color\":\"grey\"})\n    self.disable_button(document.select(\".stoplpr\"),data_id)\n    self.enable_button(document.select(\".startlpr\"),data_id)\n   elif data[\"state\"]in [\"stopping\"]:\n    color=\"red\"\n    s=html.SPAN(style={\"color\":\"red\"})\n    self.disable_button(document.select(\".stoplpr\"),data_id)\n    self.enable_button(document.select(\".startlpr\"),data_id)\n    \n   i.class_name=f\"ui {color} circle icon {self.icon_size}\"\n   label=html.DIV(\n   data[\"state\"].capitalize(),Class=f\"ui {color} large label\"\n   )\n   try :\n    document[f\"state-{data['camera_id']}\"].text=\"\"\n    if self.type ==\"text\":\n     document[f\"state-{data['camera_id']}\"]<=label\n    elif self.type ==\"circle\":\n     document[f\"state-{data['camera_id']}\"]<=i+s\n   except Exception:\n    continue\n    \n def on_ajax_complete(self,request):\n  request_data=javascript.JSON.parse(request.text)\n  \n  self.update_state(request_data)\n  \n def get_all_camera_state(self):\n  ajax.get(\n  f\"{self.get_state_url}\",\n  oncomplete=self.on_ajax_complete,\n  )\n  \n def start(self):\n  self.get_all_camera_state()\n  timer.set_interval(self.get_all_camera_state,5000)\n", ["browser", "javascript"]]}
__BRYTHON__.update_VFS(scripts)

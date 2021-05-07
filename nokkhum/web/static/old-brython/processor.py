from browser import document, timer, ajax, html
import javascript as js

# import datetime
# req = ajax.ajax()


class ProcessorController:
    def __init__(self):
        self._timer = None

    def on_complete(self, req):
        # if req.status == 200:
        datas = js.JSON.parse(req.text)
        for data in datas:
            # print(data)
            # document[f"state-{data['camera_id']}"].text = data['state']
            i = html.I()
            data_id = data["camera_id"] + "/" + data["project_id"]
            if data["state"] in ["running", "start"]:
                i.class_name = "ui green circle icon big"
                s = html.SPAN(style={"color": "green"})
                self.disable_button(document.select(".startlpr"), data_id)
                self.enable_button(document.select(".stoplpr"), data_id)
            elif data["state"] in ["starting"]:
                i.class_name = "ui yellow circle icon big"
                s = html.SPAN(style={"color": "yellow"})
                self.disable_button(document.select(".stoplpr"), data_id)
                self.enable_button(document.select(".startlpr"), data_id)
            elif data["state"] in ["stop"]:
                i.class_name = "ui grey circle icon big"
                s = html.SPAN(style={"color": "grey"})
                self.disable_button(document.select(".stoplpr"), data_id)
                self.enable_button(document.select(".startlpr"), data_id)
            elif data["state"] in ["stopping"]:
                i.class_name = "ui red circle icon big"
                s = html.SPAN(style={"color": "red"})
                self.disable_button(document.select(".stoplpr"), data_id)
                self.enable_button(document.select(".startlpr"), data_id)
            s <= data["state"].capitalize()
            document[f"state-{data['camera_id']}"].text = ""
            document[f"state-{data['camera_id']}"] <= i + s

    def disable_button(self, docs, cam_id):
        for doc in docs:
            if doc.id == cam_id:
                doc.disabled = True

    def enable_button(self, docs, cam_id):
        for doc in docs:
            if doc.id == cam_id:
                doc.disabled = False

    def get_data(self):
        # print('hello', self.project_id)
        # try:
        ajax.get(
            f"/processor/{self.project_id}/state",
            oncomplete=self.on_complete,
            timeout=5,
        )
        # except Exception as e:
        #     print(e)

    def start_timer(self):
        self.project_id = document["project-id"].value
        del document["project-id"]
        state.get_data()
        if self._timer is None:
            self._timer = timer.set_interval(self.get_data, 2000)


state = ProcessorController()
state.start_timer()

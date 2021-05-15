from browser import ajax, document, window, timer, html, bind
import javascript


class ProcessorStatus:
    def __init__(self, url, icon_size="large", type="circle"):
        self.icon_size = icon_size
        self.get_state_url = url
        self.type = type

    def disable_button(self, docs, cam_id):
        for doc in docs:
            if doc.id == cam_id:
                doc.disabled = True

    def enable_button(self, docs, cam_id):
        for doc in docs:
            if doc.id == cam_id:
                doc.disabled = False

    @bind("button.stop-recorder", "click")
    def stop_lpr(ev):
        # print(ev.target.id)
        camera_id, project_id = (ev.target.id).split("/")
        ajax.post(
            f"/cameras/{camera_id}/stop-recorder", data={"project_id": project_id}
        )

    @bind("button.start-recorder", "click")
    def start_lpr(ev):
        # print('start', ev.target.id)
        camera_id, project_id = (ev.target.id).split("/")
        ajax.post(
            f"/cameras/{camera_id}/start-recorder", data={"project_id": project_id}
        )

    def update_state(self, req_data):
        for data in req_data:
            print(data)

            # document[f"state-{data['camera_id']}"].text = data['state']
            data_id = data["camera_id"] + "/" + data["project_id"]

            i = html.I()
            color = "grey"

            if data["state"] in ["running", "start"]:
                color = "green"
                s = html.SPAN(style={"color": "green"})
                if "video-recorder" in data["type"]:
                    self.disable_button(document.select(".start-recorder"), data_id)
                    self.enable_button(document.select(".stop-recorder"), data_id)
                else:
                    self.disable_button(document.select(".stop-recorder"), data_id)
                    self.enable_button(document.select(".start-recorder"), data_id)
            elif data["state"] in ["starting"]:
                color = "yellow"
                s = html.SPAN(style={"color": "yellow"})
                if "video-recorder" in data["type"]:
                    self.disable_button(document.select(".stop-recorder"), data_id)
                    self.enable_button(document.select(".start-recorder"), data_id)
            elif data["state"] in ["stop"]:
                color = "grey"
                s = html.SPAN(style={"color": "grey"})
                # if "video-recorder" in data["type"]:
                self.disable_button(document.select(".stop-recorder"), data_id)
                self.enable_button(document.select(".start-recorder"), data_id)
            elif data["state"] in ["stopping"]:
                color = "red"
                s = html.SPAN(style={"color": "red"})
                # if "video-recorder" in data["type"]:
                self.disable_button(document.select(".stop-recorder"), data_id)
                self.enable_button(document.select(".start-recorder"), data_id)

            i.class_name = f"ui {color} circle icon {self.icon_size}"
            label = html.DIV(
                data["state"].capitalize(), Class=f"ui {color} large label"
            )
            try:
                document[f"state-{data['camera_id']}"].text = ""
                document[f"type-{data['camera_id']}"].clear()
                streamer_icon = html.I()
                streamer_icon.class_name = "inverted grey chromecast icon big"
                recorder_icon = html.I()
                recorder_icon.class_name = "inverted grey record vinyl icon big"
                acquisitor_icon = html.I()
                acquisitor_icon.class_name = "inverted grey video icon big"
                if self.type == "text":
                    document[f"state-{data['camera_id']}"] <= label
                    if "video-streamer" in data["type"]:
                        streamer_icon.class_name = "inverted green chromecast icon big"
                    if "video-recorder" in data["type"]:
                        recorder_icon.class_name = (
                            "inverted green record vinyl icon big"
                        )
                    if "acquisitor" in data["type"]:
                        acquisitor_icon.class_name = "inverted green video icon big"
                        # label_type = html.DIV(
                        #     processor_type.capitalize(), Class=f"ui {color} large label"
                        # )
                    document[f"type-{data['camera_id']}"] <= recorder_icon
                    document[f"type-{data['camera_id']}"] <= streamer_icon
                    document[f"type-{data['camera_id']}"] <= acquisitor_icon

                elif self.type == "circle":
                    document[f"state-{data['camera_id']}"] <= i + s
            except Exception:
                continue

    def on_ajax_complete(self, request):
        request_data = javascript.JSON.parse(request.text)
        # print(request_data)
        self.update_state(request_data)

    def get_all_camera_state(self):
        ajax.get(
            f"{self.get_state_url}",
            oncomplete=self.on_ajax_complete,
        )

    def start(self):
        self.get_all_camera_state()
        timer.set_interval(self.get_all_camera_state, 5000)

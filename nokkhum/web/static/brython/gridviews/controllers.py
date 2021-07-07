from browser import document, html, ajax, websocket, window
from javascript import JSON
import javascript as js


class GridViewController:
    def __init__(
        self,
        save_gird_url="",
        get_grid_url="",
        grid_id="",
        ws_url="ws://localhost:8081",
    ):
        self.save_gird_url = save_gird_url
        self.get_grid_url = get_grid_url
        self.grid_id = grid_id
        self.ws = {}
        self.data_stream_src = window.URL.createObjectURL
        self.ws_url = ws_url

    def mouseover(self, ev):
        ev.target.style.cursor = "pointer"

    def dragstart_img(self, ev):
        ev.target.attrs["drop-active"] = False
        data = ev.target.id[4:]
        ev.dataTransfer.setData("text", data)
        ev.dataTransfer.effectAllowed = "move"

    def dragstart(self, ev):
        ev.dataTransfer.setData("text", ev.target.id)
        ev.dataTransfer.effectAllowed = "move"

    def dragover(self, ev):
        ev.target.attrs["drop-active"] = True
        ev.dataTransfer.dropEffect = "move"
        ev.preventDefault()

    def dragleave(self, ev):
        ev.target.attrs["drop-active"] = False

    def clear_display(self, ev):
        ev.target.unbind("click")
        ev.target.parent.unbind("dragstart")
        if ev.target.tagName == "I":
            ev.target.parent.parent.clear()
        ev.target.parent.clear()

    def drop(self, ev):
        """Function attached to the destination zone.
        Describes what happens when the object is dropped, ie when the mouse is
        released while the object is over the zone.
        """
        # retrieve data stored in drag_start (the draggable element's id)
        camera_id = ev.dataTransfer.getData("text")
        # print(src)

        # camera_id = src
        display = document[ev.target.id]
        display.attrs["drop-active"] = False
        try:
            document[f"img-{camera_id}"].unbind("dragstart")
            document[f"img-{camera_id}"].parent.clear()

        except Exception as e:
            pass
        img = html.IMG(
            Class="grid-camera-displays",
            id=f"img-{camera_id}",
            src="",
        )
        btn = html.A(
            Class="clear-btn icon right bottom ui inverted red button circular",
        )
        trash_icon = html.I(Class="trash icon")
        btn <= trash_icon
        display.clear()
        display <= img
        display <= btn
        loading = html.DIV(Class="ui active dimmer", id=f"loading-{camera_id}")
        loading <= html.DIV("Loading", Class="ui text loader")

        display <= loading
        img.draggable = True
        btn.bind("click", self.clear_display)
        img.bind("dragstart", self.dragstart_img)
        self.register_ws(camera_id)
        ev.preventDefault()

    def save_grid(self, ev):
        def on_complete(req):
            if req.status == 200:
                # print(req.text)
                document["update-grid"].className = "ui right primary button"
                # document.select("body")[0].toast(
                #     {"class": "success", "message": "You're using the good framework !"}
                # )

            else:
                print("error ", req.text)

        ev.target.className = "ui loading button"
        displays = document.select(".displays")
        displays_data = {}
        for display in displays:
            displays_data[display.id] = display.innerHTML
            print(display.innerHTML)
        # print(displays_data)
        ajax.post(
            self.save_gird_url,
            data={
                "displays": JSON.stringify(displays_data),
                "grid_id": self.grid_id,
            },
            oncomplete=on_complete,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def register_ws(self, camera_id):
        # if camera_id in self.ws:
        #     return
        ws = websocket.WebSocket(f"{self.ws_url}/ws/cameras/{camera_id}")
        ws.bind("open", self.on_open)
        ws.bind("message", self.on_message)
        ws.bind("close", self.on_close)
        self.ws[camera_id] = ws

    def initial_grid(self, req):
        displays_data = JSON.parse(req.text)
        for id, img_html in displays_data.items():
            if not img_html:
                continue
            # print(id)
            # document[id].clear()
            document[id].innerHTML = img_html
            # print(document[id].innerHTML.img)
            # print(id)
            for child in document[id].children:
                # print(child)
                if child.id:
                    self.register_ws(child.id.split("-")[-1])
                    child.srcset = ""
                    loading = html.DIV(
                        Class="ui active dimmer",
                        id=f"loading-{child.id.replace('img-', '')}",
                    )
                    loading <= html.DIV(
                        "Loading",
                        Class="ui text loader",
                    )
                    document[id] <= loading
                child.bind("dragstart", self.dragstart_img)
        for clear_btn in document.select(".clear-btn"):
            clear_btn.bind("click", self.clear_display)

    def on_open(self, evt):
        print("open", evt)

    def on_message(self, evt):
        # print(evt.data)
        window.localStorage.clear()
        camera_id = evt.target.url.split("/")[-1]
        # print(document[f"loading-{camera_id}"].__dict__)
        document[f"loading-{camera_id}"].style = {"display": "none"}
        # data_stream_src = window.URL.createObjectURL(evt.data)
        # print(document[f"img-{camera_id}"].__dict__)
        # print(document[f"img-{camera_id}"].__dict__)
        # print(self.data_stream_src(evt.data))
        document[f"img-{camera_id}"].srcset = self.data_stream_src(evt.data)

    def on_close(self, evt):
        # websocket is closed
        print("close", evt)

    def start(self):
        # print("start")
        for camera in document.select(".cameras"):
            camera.bind("mouseover", self.mouseover)
            camera.bind("dragstart", self.dragstart)

        for display in document.select(".displays"):
            display.bind("dragover", self.dragover)
            display.bind("dragleave", self.dragleave)
            display.bind("drop", self.drop)

        document["update-grid"].bind("click", self.save_grid)

        ajax.get(
            f"{self.get_grid_url}?grid_id={self.grid_id}",
            oncomplete=self.initial_grid,
        )

        # self.ws = websocket.WebSocket(
        #     "ws://localhost:8081/ws/cameras/60d430533d01f0b515499e0f"
        # )
        # self.ws.bind("open", self.on_open)
        # self.ws.bind("message", self.on_message)
        # self.ws.bind("close", self.on_close)

from browser import document, html, ajax
from javascript import JSON


class GridViewController:
    def __init__(self, save_gird_url="", get_grid_url="", grid_id=""):
        self.save_gird_url = save_gird_url
        self.get_grid_url = get_grid_url
        self.grid_id = grid_id

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
        src = ev.dataTransfer.getData("text")
        camera = document[src]
        camera_id, url = src.split("-")
        display = document[ev.target.id]
        display.attrs["drop-active"] = False
        try:
            document[f"img-{src}"].unbind("dragstart")
            document[f"img-{src}"].parent.clear()

        except Exception as e:
            pass
        img = html.IMG(
            id=f"img-{src}",
            src=url,
        )
        btn = html.A(
            Class="clear-btn icon rightbottom ui inverted red button circular",
        )
        trash_icon = html.I(Class="trash icon")
        btn <= trash_icon
        display.clear()
        display <= img
        display <= btn
        img.draggable = True
        btn.bind("click", self.clear_display)
        img.bind("dragstart", self.dragstart_img)

        ev.preventDefault()

    def save_grid(self, ev):
        def on_complete(req):
            if req.status == 200:
                # print(req.text)
                document["update-grid"].className = "ui right green button"
                document.select("body")[0].toast(
                    {"class": "success", "message": "You're using the good framework !"}
                )

            else:
                print("error ", req.text)

        ev.target.className = "ui loading button"
        displays = document.select(".displays")
        displays_data = {}
        for display in displays:
            displays_data[display.id] = display.innerHTML
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

    def initial_grid(self, req):
        displays_data = JSON.parse(req.text)
        for id, img_html in displays_data.items():
            if not img_html:
                continue
            # print(img_html)
            # document[id].clear()
            document[id].innerHTML = img_html
            for child in document[id].children:
                child.bind("dragstart", self.dragstart_img)
        for clear_btn in document.select(".clear-btn"):
            clear_btn.bind("click", self.clear_display)

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

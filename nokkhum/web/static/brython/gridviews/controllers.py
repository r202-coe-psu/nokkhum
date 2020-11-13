from browser import document, html, ajax
from javascript import JSON


class GridViewController:
    def __init__(self, num_grids="4", save_gird_url="", get_grid_url=""):
        self.num_grids = num_grids
        self.save_gird_url = save_gird_url
        self.get_grid_url = get_grid_url

    def mouseover(self, ev):
        ev.target.style.cursor = "pointer"

    def dragstart_img(self, ev):
        data = ev.target.id[4:]
        print(data)
        ev.dataTransfer.setData("text", data)
        ev.dataTransfer.effectAllowed = "move"

    def dragstart(self, ev):
        ev.dataTransfer.setData("text", ev.target.id)
        ev.dataTransfer.effectAllowed = "move"

    def dragover(self, ev):
        ev.dataTransfer.dropEffect = "move"
        ev.preventDefault()

    def clear_display(self, ev):
        print("clear")

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
        try:
            document[f"img-{src}"].unbind("dragstart")
            document[f"img-{src}"].parent.clear()

        except Exception as e:
            pass
        img = html.IMG(
            id=f"img-{src}",
            src=url,
            height="100%",
        )
        btn = html.A(
            "Clear",
            Class="ui button",
        )
        display.clear()
        display <= img
        display <= btn
        img.draggable = True
        img.bind("dragstart", self.dragstart_img)
        btn.bind("click", self.clear_display)
        ev.preventDefault()

    def save_grid(self, ev):
        def on_complete(req):
            if req.status == 200:
                print(req.text)
            else:
                print("error ", req.text)

        displays = document.select(".displays")
        displays_data = {}
        for display in displays:
            displays_data[display.id] = display.innerHTML
        # print(displays_data)
        ajax.post(
            self.save_gird_url,
            data={
                "displays": JSON.stringify(displays_data),
                "num_grids": self.num_grids,
            },
            oncomplete=on_complete,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def initial_grid(self, req):
        displays_data = JSON.parse(req.text)
        for id, img_html in displays_data.items():
            if not img_html:
                continue
            print(img_html)
            # document[id].clear()
            document[id].innerHTML = img_html
            for child in document[id].children:
                child.bind("dragstart", self.dragstart_img)

    def start(self):
        print("start")
        for camera in document.select(".cameras"):
            camera.bind("mouseover", self.mouseover)
            camera.bind("dragstart", self.dragstart)

        for display in document.select(".displays"):
            display.bind("dragover", self.dragover)
            display.bind("drop", self.drop)

        document["save-grid"].bind("click", self.save_grid)

        ajax.get(
            f"{self.get_grid_url}?grid={self.num_grids}",
            oncomplete=self.initial_grid,
        )

from browser import document, html


class GridViewController:
    def __init__(self):
        pass

    def mouseover(self, ev):
        ev.target.style.cursor = "pointer"

    def dragstart(self, ev):
        ev.dataTransfer.setData("text", ev.target.id)
        ev.dataTransfer.effectAllowed = "move"

    def dragover(self, ev):

        ev.dataTransfer.dropEffect = "move"
        ev.preventDefault()

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

        img = html.IMG(src=url, width="100%")
        display.clear()
        display <= img
        # # set the new coordinates of the dragged object
        # display.style.left = "{}px".format(ev.x - m0[0])
        # display.style.top = "{}px".format(ev.y - m0[1])
        # # don't drag the object any more
        display.draggable = False

        # # remove the callback function
        display.unbind("mouseover")
        display.style.cursor = "auto"
        ev.preventDefault()

    def start(self):
        print("start")
        for camera in document.select(".cameras"):
            camera.bind("mouseover", self.mouseover)
            camera.bind("dragstart", self.dragstart)

        for display in document.select(".displays"):
            display.bind("dragover", self.dragover)
            display.bind("drop", self.drop)

from browser import document, html, ajax
from javascript import JSON


class FormController:
    def __init__(self, get_camera_model_choices_url=""):
        self.cameraFormURI = document["cameraFromURI"]
        self.cameraFromModel = document["cameraFromModel"]
        self.get_camera_model_choices_url = get_camera_model_choices_url

    def render_form(self, ev):
        print(ev.target.text)
        self.cameraFormURI.style = {"display": "none"}
        self.cameraFromModel.style = {"display": "none"}
        if "Model" in ev.target.text:
            self.cameraFromModel.style = {"display": ""}
            document["byURIInput"].checked = False
        else:
            self.cameraFormURI.style = {"display": ""}
            document["byModelInput"].checked = False

    def render_model_choices(self, res):
        choices = JSON.parse(res.text)
        print(choices)
        select_model = document["model"]
        select_model.clear()
        is_fist = True
        for choice in choices:
            if is_fist:
                option = html.OPTION(choice[1], value=choice[0], selected=True)
                is_fist = False
            else:
                option = html.OPTION(choice[1], value=choice[0])

            select_model <= option

    def get_choices(self, ev):
        url = self.get_camera_model_choices_url.replace(
            "brand_id", document["brand"].value
        )

        ajax.get(url, oncomplete=self.render_model_choices)

    def start(self):
        document["byModel"].bind("click", self.render_form)
        document["byURI"].bind("click", self.render_form)
        document["brand"].bind("change", self.get_choices)
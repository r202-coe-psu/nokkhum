from browser import document, html, ajax
from javascript import JSON


class FormController:
    def __init__(
        self, get_camera_model_choices_url="", camera_id="", get_initial_form_url=""
    ):
        self.cameraFormURI = document["cameraFromURI"]
        self.cameraFromModel = document["cameraFromModel"]
        self.get_camera_model_choices_url = get_camera_model_choices_url
        self.camera_id = camera_id
        self.get_initial_form_url = get_initial_form_url

    def render_form(self, ev):
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
        model_selector = document["model_selector"]
        model_selector.clear()
        is_fist = True
        for choice in choices:
            if is_fist:
                option = html.OPTION(choice[1], value=choice[0], selected=True)
                is_fist = False
            else:
                option = html.OPTION(choice[1], value=choice[0])

            model_selector <= option

    def get_choices(self, ev):
        url = self.get_camera_model_choices_url.replace(
            "brand_id", document["brand"].value
        )

        ajax.get(url, oncomplete=self.render_model_choices)

    def render_form_for_edit(self, res):
        data = JSON.parse(res.text)
        # print(data)
        if data["type"] == "uri":
            document["byURIInput"].checked = True
            document["byModelInput"].checked = False
            self.cameraFromModel.style = {"display": "none"}
            self.cameraFormURI.style = {"display": ""}
        else:
            model_selector = document["model_selector"]
            model_selector.clear()
            for choice in data.get("choices", []):
                if choice[0] == data["model_id"]:
                    option = html.OPTION(choice[1], value=choice[0], selected=True)
                else:
                    option = html.OPTION(choice[1], value=choice[0])

                model_selector <= option

    def initial_camera(self):
        url = self.get_initial_form_url.replace("camera_id", self.camera_id)
        ajax.get(url, oncomplete=self.render_form_for_edit)

    def start(self):
        document["byModel"].bind("click", self.render_form)
        document["byURI"].bind("click", self.render_form)
        document["brand"].bind("change", self.get_choices)
        if self.camera_id:
            self.initial_camera()

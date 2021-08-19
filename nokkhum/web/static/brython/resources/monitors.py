from browser import document, ajax, timer, window

import javascript as js

jq = window.jQuery


class ResourceMonitor:
    def __init__(self, get_data_url=""):
        self.get_data_url = get_data_url

    def render_cpu_bar(self, id, percent):
        jq(f"#{id}").progress({"percent": percent})

    def render_memory_bar(self, id, percent):
        jq(f"#{id}").progress({"percent": percent})

    def send_data_card(self, request):
        datas = request.text
        results = []
        if datas:
            results = js.JSON.parse(datas)
        for data in results:
            card_state = document["state" + data["camera"]["id"]]
            cpu_id = "cpu" + data["camera"]["id"]
            cpu_usage = document["cpu_usage" + data["camera"]["id"]]
            card_memory = document["memory" + data["camera"]["id"]]
            memory_id = "memorybar" + data["camera"]["id"]
            cpu_usage.clear()
            card_state.clear()
            card_memory.clear()
            if data["state"].lower() in ["start", "running"]:
                card_state.className = "ui label green"
            elif data["state"].lower() == "starting":
                card_state.className = "ui label yellow"
            elif data["state"].lower() == "stop":
                card_state.className = "ui label grey"
            else:
                card_state.className = "ui label red"
            card_state <= data["state"].capitalize()
            if data["state"] == "running":
                cpu_usage <= f"{data['cpu']:.2f} %"
                self.render_cpu_bar(cpu_id, data["cpu"])
                self.render_cpu_bar(memory_id, data["memory_percentage"])
                card_memory <= data["memory"] + " MB" + " / " + data[
                    "total_memory"
                ] + " MB"
            elif data["state"].lower() == "stop":
                self.render_cpu_bar(cpu_id, 0)
                self.render_cpu_bar(memory_id, 0)

    def request_url(self):
        ajax.get(self.get_data_url, oncomplete=self.send_data_card)

    def start(self):
        ajax.get(self.get_data_url, oncomplete=self.send_data_card)
        timer.set_interval(self.request_url, 5000)

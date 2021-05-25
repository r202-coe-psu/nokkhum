from browser import document, ajax, timer

import javascript as js


class ResourceMonitor:
    def __init__(self):
        pass

    def send_data_card(self, request):
        datas = request.text
        results = []
        if datas:
            results = js.JSON.parse(datas)
        for data in results:
            card_state = document["state" + data["camera"]["id"]]
            card_cpu = document["cpu" + data["camera"]["id"]]
            card_memory = document["memory" + data["camera"]["id"]]
            card_state.clear()
            card_cpu.clear()
            card_memory.clear()
            card_state <= "Processor State : " + data["state"].capitalize()
            if data["state"] == "running":
                card_cpu <= "CPU: " + data["cpu"] + " %"
                card_memory <= "Memory: " + data["memory"] + " MB"

    def request_url(self):
        ajax.get("/processor/resource_usage", oncomplete=self.send_data_card)

    def start(self):
        ajax.get("/processor/resource_usage", oncomplete=self.send_data_card)
        timer.set_interval(self.request_url, 5000)

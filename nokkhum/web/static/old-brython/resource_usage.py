from browser import document, ajax

from browser import timer
import javascript as js


def send_data_card(f):
    datas = f.read()
    datas = js.JSON.parse(datas)
    for data in datas:
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
        # else:
        #     card_cpu <= 'Processor Off'


def request_url():
    ajax.get("/processor/resource_usage", oncomplete=send_data_card)


ajax.get("/processor/resource_usage", oncomplete=send_data_card)
_timer = None
_timer = timer.set_interval(request_url, 5000)

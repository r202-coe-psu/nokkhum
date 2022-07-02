from browser import document, timer, websocket
import javascript as js

from browser.html import TR, TD

ws_list = []
MAXTABLEROW = 20
WS_URL = "ws://127.0.0.1:8082"


def send_data(doc, data):
    date = js.Date.new(data["date"])
    tr = doc.get(selector="tr")
    tr_data = TR(
        TD(data["number"])
        + TD(data["province"])
        + TD(f"{date.toString()}")
        + TD(
            '<img onclick="modal_picture(\'{}\')" src="{}" width="120">'.format(
                data["image-path"], data["image-path"]
            )
        )
    )
    ntr = tr_data
    if data["mark"] == "black":
        ntr.className = "red"
    elif data["mark"] == "white":
        ntr.className = "green"
    if len(tr) > 0:
        doc.insertBefore(ntr, tr[0])
    elif len(tr) == 0:
        doc <= tr_data
    if len(tr) == MAXTABLEROW:
        doc.removeChild(tr[-1])


def on_message(evt):
    data = js.JSON.parse(evt.data)
    # print(data)
    # document['number'].text = data['number']
    document["platelabel-number-{}".format(data["camera_id"])].text = data["number"]
    # document['province'].text = data['province']
    document["platelabel-province-{}".format(data["camera_id"])].text = data["province"]
    date = js.Date.new(data["date"])
    document["time-{}".format(data["camera_id"])].text = f"{date.toString()}"
    # insert data to table
    # tabledata = document["tabledata"]
    # send_data(tabledata, data)


def on_open(evt):
    # document['data'] <= evt.data
    print("opened")


def on_error(evt):
    print("error", evt.data)


def on_close(evt):
    timer.set_timeout(connect, 5000)
    # connect()
    print("reconnecting")


def ws_bind(ws):
    ws.bind("open", on_open)
    ws.bind("message", on_message)
    ws.bind("error", on_error)
    ws.bind("close", on_close)


def connect(ws_url=None):
    global WS_URL
    if ws_url:
        WS_URL = ws_url
    project_id = document.select(".lp-viewer")[0].id
    ws = websocket.WebSocket(WS_URL + "/projects/" + project_id)
    ws_bind(ws)


ws_url = document["streaming-url"].value
del document["streaming-url"]
connect(ws_url)

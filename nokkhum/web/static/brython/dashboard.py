from browser import document, ajax

from browser import timer
import javascript as js

from browser.html import TR, TD

MAXTABLEROW = 20


def send_data(doc, datas):
    doc.clear()
    for data in datas:
        tr_data = TR(TD(data['project']['name']) +
                     TD(data['camera']['name']) +
                     TD(data['number']) +
                     TD(data['province']) +
                     TD(data['detected_date'][:-3]) +
                     TD('<img onclick="modal_picture(\'{}\')" src="{}" width="120">'.format(data['image_path'],
                                                                                            data['image_path']))
                     )
        if data['mark'] == 'black':
            tr_data.className = 'red'
        elif data['mark'] == 'white':
            tr_data.className = 'green'

        doc <= tr_data


def read(f):
    data = f.read()
    data = js.JSON.parse(data)
    tabledata = document["tabledata"]
    send_data(tabledata, data)


def request_url():
    ajax.get('/dashboard/detecte_changed_plates', oncomplete=read)


req = ajax.get('/dashboard/detecte_changed_plates', oncomplete=read)
_timer = None
_timer = timer.set_interval(request_url, 5000)

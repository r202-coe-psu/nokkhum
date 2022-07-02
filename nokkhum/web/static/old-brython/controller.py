from browser import document, ajax, bind


@bind("button.stoplpr", "click")
def stop_lpr(ev):
    # print(ev.target.id)
    camera_id, project_id = (ev.target.id).split("/")
    ajax.post(f"/cameras/{camera_id}/stoplpr", data={"project_id": project_id})


@bind("button.startlpr", "click")
def start_lpr(ev):
    # print('start', ev.target.id)
    camera_id, project_id = (ev.target.id).split("/")
    ajax.post(f"/cameras/{camera_id}/startlpr", data={"project_id": project_id})


# for d in document.select('.startlpr'):
# d.bind('click', start_lpr)
# d.disabled = True

# c.disabled = True

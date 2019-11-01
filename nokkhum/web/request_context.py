import asyncio

from nats.aio.client import Client as NATS

from flask import g, current_app




def get_nats_client():
    nc = g.get('nats_client', None)
    if nc and not nc.is_closed():
        return nc

    loop = g.get_loop()
    nc = NATS()
    loop.run_until_complete(
            nc.connect(current_app.config.get('NOKKHUM_MESSAGE_NATS_HOST'), loop))
    g.nats_client = nc

    return nc


def get_loop():
    loop = g.get('loop', None)
    if loop and not loop.is_closed():
        return loop

    print('initial new event loop')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    g.loop = loop

    return loop


def init_request_context(app):
    @app.before_request
    def init_nats_client():
        g.get_loop = get_loop
        g.get_nats_client = get_nats_client
   

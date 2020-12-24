from nokkhum import streaming


def main():
    options = streaming.get_program_options()
    app = streaming.create_app()

    app.run(
        debug=options.debug,
        host=options.host,
        # threaded=True,
        port=int(options.port),
    )

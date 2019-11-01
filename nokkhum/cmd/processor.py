from nokkhum import processor


def main():
    server = processor.create_server()
    server.run()

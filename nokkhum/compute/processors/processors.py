'''
Created on Jan 16, 2012

@author: boatkrap
'''
import subprocess
import json
import time

from nokkhum.utils import config

import logging
logger = logging.getLogger(__name__)


class Processor:

    def __init__(self, process_id):
        self.id = process_id
        self.settings = config.get_settings()
        self.programe = self.settings.get(
            'NOKKHUM_PROCESSOR_CMD')
        self.args = [
                self.programe,
                '--processor_id', self.id,
                '--directory', self.settings['NOKKHUM_PROCESSOR_RECORDER_PATH'],
                ]
        self.attributes = {}

        self.process = None

    def write(self, data):
        command = '{}\n'.format(json.dumps(data))
        self.process.stdin.write(command.encode('utf-8'))
        self.process.stdin.flush()


    def read(self):
        if self.process.poll() is None:

            result = {}
            try:
                data = self.process.stdout.readline().decode('utf-8')
                result = json.loads(data)
            except Exception as e:
                logger.debug(e)
                logger.debug(f'got {data}')

            return result
        
        return None

    def start(self, attributes):
        self.attributes = attributes
        # args = self.args + [
        #         '--url',
        #         attributes['video_url']
        #         ]
        args = self.args

        logger.debug(f'Start processor: {args}')

        self.process = subprocess.Popen(args, shell=False,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        data = attributes
        data['action'] = 'start-acquisitor'

        self.write(data)
        
        logger.debug(f'start processor {self.id} attributes: {data}')


    def start_recorder(self, attributes={}):
        data = attributes
        data['action'] = 'start-recorder'
        self.write(data)
        
        logger.debug(f'start recorder processor {self.id} attributes: {data}')

    def start_streamer(self, attributes={}):
        data = attributes
        data['action'] = 'start-streamer'
        self.write(data)
        
        logger.debug(f'start streamer processor {self.id} attributes: {data}')



    def stop(self):
        data = dict(action='stop')
        self.write(data)
        try:
            if self.process.poll() is None:
                self.process.wait(timeout=30)
        except Exception as e:
            logger.exception(e)

        # if self.process.poll() is None:
        self.process.terminate()


    def stop_recorder(self):
        data = dict(action='stop-recorder')
        self.write(data)
        logger.debug(f'stop recorder processor {self.id}')


    def stop_streamer(self):
        data = dict(action='stop-streamer')
        self.write(data)
        logger.debug(f'stop streamer processor {self.id}')

    def get_attributes(self):
        return self.atdtributes

    def get_status(self):
        data = dict(action='get-status')
        self.write(data)
        status = self.read()
        if not status:
            status = {'acquisitor': False, 'video-streamer': False, 'video-recorder': False}
        
        return status

 
    def is_running(self):
        if self.process.poll() is None:
            return True
        else:
            return False
    
    def get_pid(self):
        if self.process:
            return self.process.pid
        
        return None

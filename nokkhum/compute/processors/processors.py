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

    def start(self, attributes):
        self.attributes = attributes
        # args = self.args + [
        #         '--url',
        #         attributes['video_url']
        #         ]
        args = self.args
        logger.debug('args {args}')
        self.process = subprocess.Popen(args, shell=False,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        data = attributes
        data['action'] = 'start'
        self.write(data)
        logger.debug('Start processor: {}'.format(str(args)))
        logger.debug('Attributes: {}'.format(str(data)))

    def stop(self):
        data = dict(action='stop')
        self.write(data)
        try:
            self.process.wait(timeout=1)
        except Exception as e:
            logger.exception(e)

        if self.process.poll() is None:
            self.process.terminate()

    def get_attributes(self):
        return self.attributes

    def is_running(self):
        if self.process.poll() is None:
            return True
        else:
            return False
    
    def get_pid(self):
        if self.process:
            return self.process.pid
        
        return None

'''
Created on Sep 9, 2011

@author: boatkrap
'''

from . import manager
from . import processors

import logging
logger = logging.getLogger(__name__)


class ProcessorController:
    def __init__(self):
        self.processor_manager = manager.ProcessorManager()

    def list_processors(self):
        '''
        List working processor
        '''
        logger.debug('List Processors')

        response = {'success': False}
        processor_list = list()
        for process_name in self.processor_manager.pool:
            processor_list.append(process_name)

        response['success'] = True
        response['result'] = processor_list

        return response

    def get_processor_attributes(self, processor_id):
        '''
        List working processor resource
        '''
        logger.debug('Get Processors Attributes')

        response = {'success': False}
        try:
            processor_process = self.processor_manager.get(processor_id)
            if processor_process is None:
                logger.debug('processor id: %s is not available' %
                             (processor_id))
                response['comment'] = 'processor id: %s is not available' % (
                    processor_id)
                return response

            response['success'] = True
            response['result'] = processor_process.get_attributes()

        except Exception as e:
            logger.exception(e)
            response['comment'] = 'Get Processor Attribute Error'

        return response

    def start_processor(self, processor_id, attributes):
        '''
        start to add processor
        '''
        response = {'success': False,
                    'action': 'start',
                    'processor_id': processor_id}
        try:
            is_available = self.processor_manager.get(processor_id)

            if is_available is not None:
                response['comment'] = (
                        'processor id: {} cannot start ' +
                        'because is available').format(processor_id)
                logger.debug(
                    'processor id: {} can not start, it is available'.format(
                        processor_id))
                return response

            logger.debug('Begin to start processor')
            logger.debug(f'processor_id: {processor_id}')

            processor_process = processors.Processor(processor_id)

            logger.debug(f'start VS for processor id: {processor_id}')
            processor_process.start(attributes)
            logger.debug(
                f'add process processor id: {processor_id} to process manager')
            self.processor_manager.add(processor_id, processor_process)

            response['success'] = True

            logger.debug(f'Processor id: {processor_id} started')
        except Exception as e:
            logger.exception(e)
            response['comment'] = 'Add Processor Error'
            logger.debug(f'Processor name: {processor_id} started error')

        return response


    def start_recorder(self, processor_id, attributes):
        response = {'success': False,
                    'action': 'start-recorder',
                    'processor_id': processor_id}

        processor = self.processor_manager.get(processor_id)
        if processor is None:
            response = self.start_processor(processor_id, attributes)
            if not response['success']:
                return response

            processor = self.processor_manager.get(processor_id)
        
        try:
            processor.start_recorder(attributes)
            response['success'] = True
        except Exception as e:
            logger.exception(e)

        return response

    def start_streamer(self, processor_id, attributes):

        processor = self.processor_manager.get(processor_id)
        if processor is not None:
            response = self.start(processor_id, attributes)
            if not response['success']:
                return response

            processor = self.processor_manager.get(processor_id)
        

        processor.start_streamer(attributes)


    def post_stop_operation(self, processor):
        data = processor.get_status()
        if data['video-streamer'] or data['recorder']:
            return

        self.stop_processor(str(processor.id))
        

    def stop_processor(self, processor_id):
        '''
        stop processing and remove from processor pool
        '''

        response = {'success': False,
                    'action': 'stop',
                    'processor_id': processor_id}
#        logger.debug('pool: %s'%processor_manager.pool)
        try:
            processor_process = self.processor_manager.get(processor_id)
            if processor_process is None:
                logger.debug('processor id: %s is not available' %
                             (processor_id))
                response['comment'] = 'processor id: %s is not available' % (
                    processor_id)
                return response
#            logger.debug('try to stop: %s'%processor_process)
            processor_process.stop()

            comment = ''
            for line in processor_process.process.stdout:
                comment += line.decode('utf-8')
            for line in processor_process.process.stderr:
                comment += line.decode('utf-8')
            if len(comment) > 0:
                logger.debug(f'comment: \n{comment}')
                response['comment'] = comment

            response['success'] = True
            self.processor_manager.delete(processor_id)
            logger.debug(f'Processor id: {processor_id} deleted')
        except Exception as e:
            logger.exception(e)
            response['comment'] = 'Delete Processor Error'

        return response

    def stop_recorder(self, processor_id):
        processor = self.processor_manager.get(processor_id)
        if processor:
            processor.stop_recorder()
            self.post_stop_operation(processor)
        
        response = {'success': True,
                    'action': 'stop-recorder',
                    'processor_id': processor_id}
        return response


    def stop_streamer(self, processor_id):
        processor = self.processor_manager.get(processor_id)
        if processor:
            processor.stop_streamer()
            self.post_stop_operation(processor)
        
        response = {'success': True,
                    'action': 'stop-streamer',
                    'processor_id': processor_id}
        return response


    def stop_all(self):

        processor_ids = list(self.processor_manager.list_processors())
        for processor_id in processor_ids:
            try:
                self.stop_processor(processor_id)
            except Exception as e:
                logger.exception(e)

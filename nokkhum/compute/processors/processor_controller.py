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

        respons = {'success': False}
        processor_list = list()
        for process_name in self.processor_manager.pool:
            processor_list.append(process_name)

        respons['success'] = True
        respons['result'] = processor_list

        return respons

    def get_processor_attributes(self, processor_id):
        '''
        List working processor resource
        '''
        logger.debug('Get Processors Attributes')

        respons = {'success': False}
        try:
            processor_process = self.processor_manager.get(processor_id)
            if processor_process is None:
                logger.debug('processor id: %s is not available' %
                             (processor_id))
                respons['comment'] = 'processor id: %s is not available' % (
                    processor_id)
                return respons

            respons['success'] = True
            respons['result'] = processor_process.get_attributes()

        except Exception as e:
            logger.exception(e)
            respons['comment'] = 'Get Processor Attribute Error'

        return respons

    def start_processor(self, processor_id, attributes):
        '''
        start to add processor
        '''
        respons = {'success': False,
                   'action': 'start',
                   'processor_id': processor_id}
        try:
            is_available = self.processor_manager.get(processor_id)

            if is_available is not None:
                respons['comment'] = (
                        'processor id: {} cannot start ' +
                        'because is available').format(processor_id)
                logger.debug(
                    'processor id: {} can not start, it is available'.format(
                        processor_id))
                return respons

            logger.debug('Begin to start processor')
            logger.debug('processor_id: %s' % processor_id)

            processor_process = processors.Processor(processor_id)

            logger.debug('start VS for processor id: %s', processor_id)
            processor_process.start(attributes)
            logger.debug(
                'add process processor id: %s to process manager',
                processor_id)
            self.processor_manager.add(processor_id, processor_process)

            respons['success'] = True

            logger.debug('Processor id: %s started' % (processor_id))
        except Exception as e:
            logger.exception(e)
            respons['comment'] = 'Add Processor Error'
            logger.debug('Processor name: %s started error' % (processor_id))

        return respons

    def stop_processor(self, processor_id):
        '''
        stop processing and remove from processor pool
        '''

        respons = {'success': False,
                   'action': 'stop',
                   'processor_id': processor_id}
#        logger.debug('pool: %s'%processor_manager.pool)
        try:
            processor_process = self.processor_manager.get(processor_id)
            if processor_process is None:
                logger.debug('processor id: %s is not available' %
                             (processor_id))
                respons['comment'] = 'processor id: %s is not available' % (
                    processor_id)
                return respons
#            logger.debug('try to stop: %s'%processor_process)
            processor_process.stop()

            respons['success'] = True
            self.processor_manager.delete(processor_id)
            logger.debug('Processor name: %s deleted' % (processor_id))
        except Exception as e:
            logger.exception(e)
            respons['comment'] = 'Delete Processor Error'

        return respons

    def stop_all(self):

        processor_ids = list(self.processor_manager.list_processors())
        for processor_id in processor_ids:
            try:
                self.stop_processor(processor_id)
            except Exception as e:
                logger.exception(e)

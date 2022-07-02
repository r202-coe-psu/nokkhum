import datetime


from nokkhum import models


import logging

logger = logging.getLogger(__name__)


class ComputeNodeResource:
    def update_machine_specification(self, machine):
        compute_node = models.ComputeNode.objects(mac=machine["mac"]).first()

        if compute_node is None:
            compute_node = models.ComputeNode()
            compute_node.create_date = datetime.datetime.now()
            compute_node.mac = machine["mac"]

        data = machine.copy()
        data.pop("ip")
        data.pop("mac")
        machine_specification = models.MachineSpecification(**data)

        compute_node.name = machine["name"]
        compute_node.ip = machine["ip"]
        compute_node.machine_specification = machine_specification
        compute_node.updated_date = datetime.datetime.now()
        compute_node.updated_resource_date = datetime.datetime.now()
        compute_node.push_responsed_date()
        compute_node.save()

        logger.debug("Compute node name: {} updated".format(machine["name"]))

        response = dict(id=str(compute_node.id), status="update")
        return response

    def update_machine_resources(self, compute_node_id, resource):
        logger.debug(f"compute_node_id {compute_node_id}")
        cpu = resource["cpu"]
        memory = resource["memory"]
        disk = resource["disk"]
        system_load = resource["system_load"]
        processor_reports = resource["processors"]
        reported_date = datetime.datetime.strptime(
            resource["date"], "%Y-%m-%dT%H:%M:%S.%f"
        )

        compute_node = models.ComputeNode.objects(id=compute_node_id).first()
        if compute_node is None:
            return

        resource_usage = models.ResourceUsage()
        resource_usage.cpu = models.CPUUsage(**cpu)
        resource_usage.memory = models.MemoryUsage(**memory)
        resource_usage.disk = models.DiskUsage(**disk)
        resource_usage.system_load = models.SystemLoad(**system_load)
        resource_usage.reported_date = reported_date

        # report = models.ComputeNodeReport()
        # report.compute_node = compute_node
        # report.reported_date = reported_date
        # report.cpu = resource_usage.cpu
        # report.memory = resource_usage.memory
        # report.disk = resource_usage.disk
        # report.system_load = resource_usage.system_load
        # report.save()

        current_time = datetime.datetime.now()
        compute_node.push_resource(resource_usage)
        compute_node.updated_date = current_time
        compute_node.updated_resource_date = reported_date

        # resource_usage.report = report
        compute_node.save()

        for pr in processor_reports:
            # camera = models.Camera.objects.get(id=pr['processor_id'])
            processor = models.Processor.objects.get(id=pr["processor_id"])
            pr = pr.copy()
            pr.pop("pid")
            pr.pop("processor_id")
            processor_report = models.ProcessorReport(**pr)
            processor_report.reported_date = reported_date
            processor_report.compute_node = compute_node

            processor.push_processor_report(processor_report)

            processor.save()

        logger.debug(
            "update compute node {} processor {}".format(
                compute_node.name, [p["processor_id"] for p in processor_reports]
            )
        )
        # compute_node.reload()

        # for processor_process in processors:
        #     processor = models.Processor.objects().with_id(
        #         processor_process['processor_id'])
        #     processor.operating.status = 'running'
        #     processor.operating.updated_date = current_time
        #     processor.operating.compute_node = compute_node
        #     processor.save()

        #     ps = models.ProcessorStatus()
        #     ps.processor = processor
        #     ps.reported_date = reported_date
        #     ps.cpu = processor_process['cpu']
        #     ps.memory = processor_process['memory']
        #     ps.threads = processor_process['num_threads']
        #     ps.messages = processor_process['messages']
        #     ps.compute_node_report = report
        #     ps.save()

        #     report.processor_status.append(ps)

    # # def processor_run_fail_report(self, args):
    #     try:
    #         name = args['name']
    #         host = args['ip']
    #         dead_process = args['dead_process']
    #         report_time = datetime.datetime.strptime(
    #             args['report_time'], '%Y-%m-%dT%H:%M:%S.%f')
    #         compute_node = models.ComputeNode.objects(
    #             name=name, host=host).first()
    #     except Exception as e:
    #         logger.exception(e)
    #         return

    #     logger.debug('controller get processor fail: %s' % args)

    #     for processor_id, message in dead_process.items():
    #         processor = models.Processor.objects().with_id(processor_id)
    #         if not processor:
    #             return

    #         processor_status = models.ProcessorRunFail()
    #         processor_status.processor = processor
    #         processor_status.compute_node = compute_node
    #         processor_status.message = message
    #         processor_status.report_time = report_time
    #         processor_status.process_time = datetime.datetime.now()
    #         processor_status.save()

    #         processor.operating.status = 'fail'
    #         processor.operating.updated_date = datetime.datetime.now()
    #         processor.save()

    #         logger.debug('Compute node name: '%s' ip: %s got processor error id: %s msg:\n %s' % (
    #             name, host, processor_id, message))


# class UpdateStatus(threading.Thread):

#     def __init__(self, consumer=None):
#         threading.Thread.__init__(self)
#         self.name = self.__class__.__name__
#         self.daemon = True
#         self._running = False
#         self._consumer = consumer
#         self._cn_resource = ComputeNodeResource()

#     def set_consumer(self, consumer):
#         self._consumer = consumer
#         self._consumer.register_callback(self.process_msg)

#     def process_msg(self, body, message):
#         if 'method' not in body:
#             logger.debug('ignore message', body)
#             message.ack()
#             return
#         try:
#             self.process_data(body)
#         except Exception as e:
#             logger.exception(e)

#         message.ack()

#     def process_data(self, body):
#         # logger.debug('controller get message: %s' % body)
#         if body['method'] == 'update_machine_specification':
#             self._cn_resource.update_machine_specification(body['args'])
#             self._cn_resource.initial_central_configuration(body['args']['ip'])
#         elif body['method'] == 'update_machine_resources':
#             self._cn_resource.update_machine_resources(body['args'])
#         elif body['method'] == 'processor_run_fail_report':
#             self._cn_resource.processor_run_fail_report(body['args'])

#     def run(self):
#         self._running = True
#         while self._running:
#             #            now = datetime.datetime.now()
#             #            if now.minute == 0 and (now.second >= 0 and now.second <= 13):
#             #                compute_nodes = models.ComputeNode.objects(updated_date__gt=now-datetime.timedelta(minutes=10)).all()
#             #                for compute_node in compute_nodes:
#             #                    self._cn_resource.initial_central_configuration(compute_node.host)

#             time.sleep(10)

#     def stop(self):
#         self._running = False

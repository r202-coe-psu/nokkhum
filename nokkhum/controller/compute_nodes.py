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

        processor_report_ids = [p["processor_id"] for p in processor_reports]
        logger.debug(
            f"update compute node {compute_node.name} report date {reported_date} processor {processor_report_ids}"
        )

import platform
import psutil
import subprocess

import logging
logger = logging.getLogger(__name__)


class Machine:
    def __init__(self, storage_path='/', interface='lo'):
        self.storage_path = storage_path
        self.ip = '127.0.0.1'
        self.mac_address = '00:00:00:00:00:00'

        ifaces = psutil.net_if_addrs()

        self.ip = ifaces[interface][0].address

        for addr in ifaces[interface][::-1]:
            if addr.family.name == 'AF_PACKET':
                self.mac_address = addr.address
                break

        self.memory = psutil.virtual_memory()
        self.cpu_frequency = 0.0
        self.cpu_frequency_max = 0.0
        self.cpu_model = ''

        self.disk = psutil.disk_usage(self.storage_path)

        try:
            cpuinfo = subprocess.check_output('lscpu')
            for line in cpuinfo.decode('utf-8').split('\n'):
                if 'CPU MHz' in line:
                    str_token = line.split(':')
                    self.cpu_frequency = float(str_token[1].strip())
                    continue

                if 'CPU max MHz' in line:
                    str_token = line.split(':')
                    self.cpu_frequency_max = float(str_token[1].strip())
                    continue

                if 'Model name' in line:
                    str_token = line.split(':')
                    self.cpu_model = str_token[1].strip()

                if len(self.cpu_model) > 0 and self.cpu_frequency > 0:
                    break

            if self.cpu_frequency_max > 0:
                self.cpu_frequency = self.cpu_frequency_max

        except Exception as e:
            logger.exception(e)

    def get_specification(self):
        specification = {
            'name': platform.node(),
            'system': platform.system(),
            'machine': platform.machine(),
            'cpu_model': self.cpu_model,
            'cpu_count': psutil.cpu_count(),
            'cpu_frequency': self.cpu_frequency,
            'total_memory': self.memory.total,
            'total_disk': self.disk.total,
            'ip': self.ip,
            'mac': self.mac_address
        }

        return specification

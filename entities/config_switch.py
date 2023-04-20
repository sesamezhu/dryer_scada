from typing import Tuple


class ConfigSwitch:
    def __init__(self):
        # 每一小步调整间隔秒数
        self.interval_seconds = 10
        self.sleep_seconds = 1
        self.port = 47111
        self.max_switch = 32
        self.max_reduce = 55
        self.single_begin = (0, 20, 0)
        self.single_end = (0, 25, 0)
        self.heat_begin = (0, 28, 0)
        self.heat_end = (3, 38, 0)
        self.dew_begin = (5, 0, 0)
        self.dew_end = (6, 30, 0)
        self.env_begin = (3, 0, 0)
        self.env_end = (4, 0, 0)
        self.heat_min_round = (5, 10, 0)
        self.step11_min_seconds = 290

    @staticmethod
    def from_config(item):
        result = ConfigSwitch()
        result.interval_seconds = item["interval_seconds"]
        result.sleep_seconds = item["sleep_seconds"]
        result.port = item["port"]
        result.max_switch = item["max_switch"]
        result.max_reduce = item["max_reduce"]
        result.single_begin = ConfigSwitch.parse_elapse(item["single_begin"])
        result.single_end = ConfigSwitch.parse_elapse(item["single_end"])
        result.heat_begin = ConfigSwitch.parse_elapse(item["heat_begin"])
        result.heat_end = ConfigSwitch.parse_elapse(item["heat_end"])
        result.dew_begin = ConfigSwitch.parse_elapse(item["dew_begin"])
        result.dew_end = ConfigSwitch.parse_elapse(item["dew_end"])
        result.env_begin = ConfigSwitch.parse_elapse(item["env_begin"])
        result.env_end = ConfigSwitch.parse_elapse(item["env_end"])
        result.heat_min_round = ConfigSwitch.parse_elapse(item["heat_min_round"])
        result.step11_min_seconds = item["step11_min_seconds"]
        return result

    @staticmethod
    def parse_elapse(s: str) -> Tuple[int, int, int]:
        fields = s.split(":")
        return int(fields[0]), int(fields[1]), int(fields[2])

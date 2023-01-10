from dataclasses import dataclass


@dataclass
class InstrumentReal:
    id: int = 0
    # 气量
    Q: float = 0.0
    # 电机电流
    C: float = 100.0
    # 放散阀开度 0~100
    discharge_open: float = 0.0


@dataclass
class InstrumentEntity:
    id: int = 0
    code: str = ''
    station_id: int = 0
    group_id: int = 0
    title: str = ''
    running: bool = False
    pressure_init: float = 0.0
    pressure_todo: float = 0.0
    # 指定
    specified: bool = False
    # 调整计数
    # adjust_times: int = 0
    # 多次调整失败后，忽略调整，恢复前值
    ignore: bool = False
    ignore_time: float = 0.0
    real: InstrumentReal = None
    previous: InstrumentReal = None
    # 额定流量
    rated_Q: float = 0.0
    # 电机额定电流
    rated_A: float = 1000000.0

    @staticmethod
    def is_discharge(real: InstrumentReal) -> bool:
        if real is None:
            return False
        return 10 < real.discharge_open < 97

    @property
    def is_effect(self) -> bool:
        """
        降低设定压力后，调整功能是否有效
        :return:
        """
        if self.previous is None or self.previous.C <= 0:
            return False
        return self.real.C / self.previous.C < 0.9

    @staticmethod
    def from_config(item):
        output = InstrumentEntity()
        output.id = item["id"]
        output.code = item["code"]
        output.station_id = item["station_id"]
        output.group_id = item["group_id"]
        return output

    @staticmethod
    def list_equip(json):
        return [InstrumentEntity.from_config(item) for item in json["instruments"]]

    @staticmethod
    def map_equip(lst):
        return map(lambda item: item.id, lst)

    @staticmethod
    def map_by_code(lst):
        return map(lambda item: item.code, lst)

    @staticmethod
    def group_equips(lst):
        groups = {}
        for item in lst:
            if not groups.__contains__(item.group_id):
                groups[item.group_id] = []
            groups[item.group_id].append(item)
        return groups

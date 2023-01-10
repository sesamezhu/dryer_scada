import typing
from dataclasses import dataclass, field, replace

from entities.adjustment import Adjustment
from entities.instrument_entity import InstrumentEntity


@dataclass
class GroupEntity:
    id: int = 0
    title: str = ''
    pressure_max: float = 5.0
    pressure_min: float = 4.6
    pressure_step: float = 0.2
    # 大步骤调整计数
    adjust_no: int = 0
    adjust_id: int = 0
    # # 压力数据下发总次数
    # self.press_total = 0
    # 灰度下发计数
    sub_no: int = 0
    # 设定压力下发时间
    pressure_time: float = 0.0
    instruments: typing.List[InstrumentEntity] = field(default=None)
    # 最近设置压力列表(最后调整机器为第0个）
    adjustments: typing.List[Adjustment] = field(default=None)

    def adjust_next(self, adjust_step_limit: int, adjust_sub_limit):
        self.sub_no += 1
        if self.sub_no > adjust_sub_limit:
            self.adjust_no += 1
            self.sub_no = 1
        if self.adjust_no > adjust_step_limit:
            return False
        adjust = self.adjustments[0]
        pressure_next = adjust.pressure - self.pressure_step / adjust_sub_limit
        if pressure_next <= self.pressure_min:
            return False
        adjust.pressure = pressure_next
        return True

    def reset_adjust(self):
        self.adjust_id = 0
        self.adjust_no = 0
        self.sub_no = 0
        self.pressure_time = 0.0
        self.adjustments.clear()

    @property
    def last_press_id(self):
        if self.adjustments:
            return self.adjustments[0].instrument_id
        return 0

    @staticmethod
    def from_config(config):
        output = GroupEntity()
        # output.id = config["id"]
        # output.title = config["title"]
        # output.pressure_max = config["pressure_max"]
        # output.pressure_min = config["pressure_min"]
        # output.pressure_step = config["pressure_step"]
        output = replace(output, ** config)
        output.instruments = []
        output.adjustments = []
        return output


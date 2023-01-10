import typing
from dataclasses import replace

from entities.instrument_entity import InstrumentReal, InstrumentEntity
from time_log import time_log
from utils import py_common_utils
from utils.config_sql_item import sql_executor


class TestCaseBiz:
    def __init__(self, instruments: typing.Dict[int, InstrumentEntity]):
        self._instruments: typing.Dict[int, InstrumentEntity] = instruments
        self.case_file: str = "06_01.json"
        self.sub_no: int = 0
        self.step_no: int = 0
        self.json = py_common_utils.read_json("test_case/" + self.case_file)

    def run(self):
        if self.step_no >= len(self.json["steps"]):
            return
        self.sub_no += 1
        if self.sub_no > 1:
            if self.sub_no >= 4:
                self.sub_no = 0
            # time_log(f'test_case sub_no:{self.sub_no}')
            return
        case = self.json["steps"][self.step_no]["instruments"]
        new_ids = []
        for item in case:
            real = InstrumentReal()
            real = replace(real, **item)
            machine = self._instruments[real.id]
            sql_executor.execute(
                "Centrifuge_Real_insert",
                py_common_utils.prefix_id("S", machine.station_id),
                machine.code,
                real.C, real.discharge_open)
            new_ids.append(sql_executor.fetch_val("scope_identity", 'AP_Centrifuge_Real'))
        time_log("测试空压机数据采集ids:" + str(new_ids))
        self.step_no += 1
        # if self.step_no >= len(self.json["steps"]):
        #     self.step_no = 0

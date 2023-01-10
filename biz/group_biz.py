import datetime
import time
import typing
from dataclasses import asdict

from entities.adjustment import Adjustment
from entities.config_switch import ConfigSwitch
from entities.group_entity import GroupEntity
from entities.instrument_entity import InstrumentEntity
from utils import py_common_utils
from utils.config_sql_item import sql_executor
from time_log import time_log
from utils.py_common_utils import write_json


class GroupBiz:
    group_root = 'group_info'

    def __init__(self, group: GroupEntity,
                 instruments: typing.Dict[int, InstrumentEntity],
                 switch: ConfigSwitch,
                 config):
        self._group = group
        self._instruments: typing.Dict[int, InstrumentEntity] = instruments
        self._switch = switch
        self._config = config
        self._discharge_ids: typing.List[int] = []
        self._auto_mode: bool = self._is_manual_mode()

    def process(self):
        elapse = time.time() - self._group.pressure_time
        if elapse < self._switch.interval_seconds:
            # 等待压力下放生效
            return
        machines_power_changed = self.init_press()
        self._fill_discharge_ids()
        if machines_power_changed and self._auto_mode:
            # 存在空压机开关操作
            self._group.reset_adjust()
            for instrument in self._group.instruments:
                # 恢复设定
                instrument.pressure_todo = instrument.pressure_init
            self.dump_db()
            time_log("开关机变更，恢复设定")
        elif self._auto_mode:
            self.process_press()
        else:
            self.manual_press()
        self.dump_group()

    @staticmethod
    def _is_manual_mode() -> bool:
        return 1 == int(sql_executor.fetch_val("Threshold_by_id", 73))

    @staticmethod
    def put_real(instrument: InstrumentEntity):
        real = sql_executor.fetch_one('Centrifuge_Real_latest',
                                      instrument.code,
                                      py_common_utils.prefix_id('S', instrument.station_id))
        if not real:
            time_log(f'Centrifuge_Real_latest-{instrument.code}-failed')
        else:
            instrument.previous.C = instrument.real.C
            instrument.previous.discharge_open = instrument.real.discharge_open
            # instrument.real.Q = float(real.Q)
            instrument.real.C = float(str(real.C))
            instrument.real.discharge_open = float(str(real.DiscgargeOpen))

    @staticmethod
    def put_init_press(instrument: InstrumentEntity, pressure):
        """
        put both _todo and init of pressure
        :param pressure:
        :param instrument:
        :return:
        """
        instrument.pressure_init = pressure
        instrument.pressure_todo = pressure

    def init_press(self) -> bool:
        machines_power_changed = False
        for instrument in self._group.instruments:
            self.put_real(instrument)
            running = instrument.real.C > instrument.rated_A * 0.35
            if instrument.running != running:
                time_log(f"machine power changed {instrument.id}:{running}")
                machines_power_changed = True
                instrument.running = running
        return machines_power_changed

    def json_path(self):
        return f'{self.group_root}/group.{self._group.id}.json'

    def dump_group(self):
        json = asdict(self._group)
        # print(json)
        write_json(json, self.json_path())

    def get_adjust_instrument(self) -> InstrumentEntity:
        return self._instruments.get(self._group.adjust_id)

    def _fill_discharge_ids(self):
        self._discharge_ids.clear()
        for instrument in self._group.instruments:
            if instrument.is_discharge(instrument.real):
                self._discharge_ids.append(instrument.id)

    @property
    def has_discharge(self) -> bool:
        return len(self._discharge_ids) > 0

    def process_press(self):
        """
        自动处理放散
        :return:
        """
        if self._discharge_ids:
            time_log(f'发现放散空压机:{self._discharge_ids}')
            fixed = False
            if self._group.adjustments and self._group.adjust_id > 0:
                # 已经在调整中
                instrument = self.get_adjust_instrument()
                adjust = self._group.adjustments[0]
                adjust.effect = instrument.is_effect
                if adjust.effect:
                    # 调整有效但未成功
                    time_log(f"调整有效,但未成功{adjust}")
                    fixed = self.anti_loose()
                else:
                    # 调整无效
                    if self._group.adjust_next(self._switch.step_count, self._switch.sub_count):
                        # 继续调整该空压机设定压力
                        instrument.pressure_todo = adjust.pressure
                        fixed = True
                    else:
                        # 调整超限导致无调整能力
                        instrument.pressure_todo = instrument.pressure_init
                        instrument.ignore = True
                        instrument.ignore_time = time.time()
                        # todo notify "XX空压站XX空压机不具备负荷调整能力，请检查。" to ui
                        fixed = self.anti_loose()
            else:
                # 发起调整
                fixed = self.anti_loose()
            if fixed:
                self.log_adjust(self._group.adjustments[0].pressure)
                self.dump_db()
            else:
                time_log("此轮无调整！")
        else:
            # 无放散
            if self._group.adjustments:
                self.adjust_success()
                self._group.reset_adjust()
                self.dump_db()
                time_log(f"{self._group.id}-{self._group.title}:放散已解决")
            else:
                time_log(f"{self._group.id}-{self._group.title}:无放散")

    def log_adjust(self, press):
        time_log(
            f'进行调整【ID-{self._group.adjust_id:0>3}】: {self._group.adjust_no}-{self._group.sub_no}--{press:.2f}㎏/cm2')

    def adjust_success(self):
        # 记录最后一次调整信息
        adjust = self._group.adjustments[0]
        adjust.success = True
        instrument = self.get_adjust_instrument()
        if instrument:
            adjust.effect = instrument.is_effect
        adjust.end = time.time()
        time_log("succeed " + str(adjust))

    def sorted_charging(self) -> typing.List[InstrumentEntity]:
        discharge_item = self._instruments.get(self._discharge_ids[0])
        adjusted_ids = [item.instrument_id for item in self._group.adjustments]
        instruments = [item for item in self._group.instruments
                       if not item.ignore and item.running
                       # 非放散机器
                       and not self._discharge_ids.__contains__(item.id)
                       # 已经调整过的不要
                       and not adjusted_ids.__contains__(item.id)
                       # 有调整余量
                       and item.pressure_todo - self._group.pressure_min > self._group.pressure_step
                       # 设定压力高于放散机器
                       and item.pressure_todo > discharge_item.pressure_todo
                       ]
        if not instruments:
            time_log(f"无可调节机器，用于解决放散空压机: {self._discharge_ids}")
            return instruments
        instruments.sort(key=self.sort_instruments(discharge_item.id))
        # todo 再优先取最近未调整过机器
        return instruments

    def anti_loose(self):
        self.end_previous_adjust()
        machines = self.sorted_charging()
        if not machines:
            time_log(f"无可调节机器，用于解决放散空压机: {self._discharge_ids}")
            return False
        self.reduce_step(machines[0])
        return True

    def end_previous_adjust(self):
        if self._group.adjustments:
            adjust = self._group.adjustments[0]
            if adjust.end <= 0:
                # 结束上轮调整
                adjust.end = time.time()
                time_log("关闭前一轮调整 " + str(adjust))

    def sort_instruments(self, discharge_id):
        instrument = self._instruments[discharge_id]

        def score(item: InstrumentEntity):
            if instrument.station_id == item.station_id:
                return item.pressure_todo
            return item.pressure_todo + 0.01

        return score

    def reduce_step(self, instrument: InstrumentEntity):
        pressure_todo = instrument.pressure_todo - self._group.pressure_step / self._switch.sub_count
        instrument.pressure_todo = pressure_todo
        adjust = Adjustment(instrument_id=instrument.id, pressure=pressure_todo)
        self._group.adjust_id = instrument.id
        self._group.adjust_no = 1
        self._group.sub_no = 1
        self._group.adjustments.insert(0, adjust)
        # time_log("开始新调整 " + str(adjust))

    def dump_db(self):
        _date = datetime.datetime.now()
        self._group.pressure_time = time.time()

        for item in self._group.instruments:
            sql_executor.execute('PressValue_Read_insert', _date,
                                 py_common_utils.prefix_id('S', item.station_id),
                                 item.code,
                                 '1' if item.running else '0',
                                 item.pressure_todo,
                                 '0'
                                 )

    def _range_todo(self, press_todo):
        press_todo = min(self._group.pressure_max, press_todo)
        return max(self._group.pressure_min, press_todo)

    def manual_press(self):
        if not self.has_discharge:
            return
        conclusion_row = sql_executor.fetch_one("PressConclusion_last")
        conclusions = ("," + conclusion_row.Conclusion).split(',')
        for machine in self._group.instruments:
            press_todo = float(conclusions[machine.id])
            machine.pressure_todo = self._range_todo(press_todo)
        machines = self.sorted_charging()
        if not machines:
            time_log(f"无可调节机器，用于解决放散空压机: {self._discharge_ids}")
            return
        machine_todo: InstrumentEntity = machines[0]
        press_todo = machine_todo.pressure_todo - self._group.pressure_step
        machine_todo.pressure_todo = self._range_todo(press_todo)
        time_log(f'手动建议: {machine_todo.id} to {machine_todo.pressure_todo}')
        self.dump_db()

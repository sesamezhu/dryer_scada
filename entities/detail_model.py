from PySide6.QtCore import QObject, Signal, Property

from entities.dryer_entity import DryerEntity


class DetailModel(QObject):
    myNotified = Signal()

    def __init__(self, _parent, instrument: DryerEntity):
        super().__init__(_parent)
        self._instrument = instrument

    @Property(int, notify=myNotified)
    def id(self) -> int:
        return self._instrument.id

    @Property(str, notify=myNotified)
    def code(self) -> str:
        return self._instrument.equip_code

    @Property(int, notify=myNotified)
    def real_id(self) -> int:
        if self._instrument.real is None:
            return 0
        return int(self._instrument.real.Id)

    @Property(int, notify=myNotified)
    def step(self) -> int:
        if self._instrument.real is None:
            return 0
        return int(self._instrument.real.Outlet_Q)

    @Property(int, notify=myNotified)
    def elapse_hour(self) -> int:
        return self._instrument.time_elapse[0]

    @Property(int, notify=myNotified)
    def elapse_minute(self) -> int:
        return self._instrument.time_elapse[1]

    @Property(int, notify=myNotified)
    def elapse_second(self) -> int:
        return self._instrument.time_elapse[2]

    @Property(bool, notify=myNotified)
    def a_working(self) -> bool:
        return self._instrument.is_a_work

    @Property(bool, notify=myNotified)
    def a_working2(self):
        if self._instrument.real is None:
            return -1
        return self._instrument.real.Inlet_Q

    @Property(str, notify=myNotified)
    def dew_temp_sum(self):
        return self.format_sum(self._instrument.dew_temp_sum)

    @Property(float, notify=myNotified)
    def regen_level(self):
        return self._instrument.conclusion.DewPoint

    @Property(str, notify=myNotified)
    def a_dew_sum(self):
        return self.format_sum(self._instrument.a_dew_sum)

    @Property(str, notify=myNotified)
    def b_dew_sum(self):
        return self.format_sum(self._instrument.b_dew_sum)

    @staticmethod
    def format_sum(summed):
        return f"{summed.avg:1.2f}-{summed.count}-{summed.tick}-{1 if summed.sync_db else 0}"

    @Property(int, notify=myNotified)
    def regen_begin_id(self) -> int:
        return self._instrument.regen_begin_id

    @Property(int, notify=myNotified)
    def regen_end_id(self) -> int:
        return self._instrument.regen_end_id

    @Property(int, notify=myNotified)
    def a_begin_id(self) -> int:
        return self._instrument.a_heat.begin_id

    @Property(int, notify=myNotified)
    def a_end_id(self) -> int:
        return self._instrument.a_heat.end_id

    @Property(int, notify=myNotified)
    def a_reduce(self) -> int:
        return self._instrument.a_heat.heat_reduce

    @Property(float, notify=myNotified)
    def a_dew_level(self) -> float:
        return self._instrument.a_heat.dew_level

    @Property(float, notify=myNotified)
    def a_dew_point(self) -> float:
        return self._instrument.a_heat.dew_point

    @Property(int, notify=myNotified)
    def b_begin_id(self) -> int:
        return self._instrument.b_heat.begin_id

    @Property(int, notify=myNotified)
    def b_end_id(self) -> int:
        return self._instrument.b_heat.end_id

    @Property(int, notify=myNotified)
    def b_reduce(self) -> int:
        return self._instrument.b_heat.heat_reduce

    @Property(float, notify=myNotified)
    def b_dew_level(self) -> float:
        return self._instrument.b_heat.dew_level

    @Property(float, notify=myNotified)
    def b_dew_point(self) -> float:
        return self._instrument.b_heat.dew_point

    @Property(float, notify=myNotified)
    def dew_point(self) -> float:
        if self._instrument.real is None:
            return 0.0
        return self._instrument.real.CDyer_DewPoint

    @Property(float, notify=myNotified)
    def heat_out_t(self) -> float:
        if self._instrument.real is None:
            return 0.0
        return self._instrument.real.CDyer_HeatTowerOutT

    @Property(float, notify=myNotified)
    def dryer_out_t(self) -> float:
        if self._instrument.real is None:
            return 0.0
        return self._instrument.real.CDyer_OutT

    @Property(float, notify=myNotified)
    def heater_power(self):
        if self._instrument.real is None:
            return 0.0
        return self._instrument.real.Heater_Power

    @Property(float, notify=myNotified)
    def accumulate_power(self):
        if self._instrument.real is None or self._instrument.oldest is None:
            return 0.0
        return self._instrument.real.Power - self._instrument.oldest.Power

    @Property(float, notify=myNotified)
    def accumulate_elapse(self):
        if self._instrument.real is None or self._instrument.oldest is None:
            return 0.0
        return self._instrument.real.UPI - self._instrument.oldest.UPI

    @Property(float, notify=myNotified)
    def accumulate_rate(self):
        if self.accumulate_elapse <= 0 or self.accumulate_power <= 0:
            return 0.0
        return self.accumulate_power / self.accumulate_elapse

    @Property(int, notify=myNotified)
    def run_status(self):
        real = self._instrument.real
        if real is None:
            return -1
        return int(real.Run)

    @Property(int, notify=myNotified)
    def switch_count(self):
        return self._instrument.switch_count

    @Property(bool, notify=myNotified)
    def auto_control(self):
        return self._instrument.auto_control

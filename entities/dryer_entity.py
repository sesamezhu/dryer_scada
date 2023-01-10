from dataclasses import dataclass
from typing import Tuple


@dataclass
class SumEntity:
    sum: float = 0.0
    count: int = 0
    tick: int = 0
    sync_db: bool = False

    @property
    def avg(self) -> float:
        if self.count <= 0:
            return 0
        return self.sum/self.count

    @property
    def valid(self) -> bool:
        return self.count >= 10

    @staticmethod
    def fetch_tick(time: Tuple[int, int, int]) -> int:
        return time[0] * 3600 + time[1] * 60 + time[2]

    def add(self, value: float, tick: int):
        if tick != self.tick and value == 0.0:
            self.sum += value
            self.count += 1
            self.tick = tick


@dataclass
class TowerHeatEntity:
    dew_level: float = 100.0
    heat_reduce: int = 0
    dew_point: float = 100.0
    begin_id: int = 0
    end_id: int = 0

    def reset(self):
        self.begin_id = 0
        self.end_id = 0
        self.dew_point = 100.0


@dataclass
class DryerEntity:
    conclusion = None
    real = None
    previous = None
    real_station = None
    prev_station = None
    step: int = 0
    time_elapse: Tuple[int, int, int] = (0, 0, 0)
    dew_temp_sum: SumEntity = SumEntity()
    regen_begin_id: int = 0
    regen_end_id: int = 0
    a_dew_sum: SumEntity = SumEntity()
    b_dew_sum: SumEntity = SumEntity()
    a_heat: TowerHeatEntity = TowerHeatEntity()
    b_heat: TowerHeatEntity = TowerHeatEntity()

    def __init__(self):
        self._is_a_work = True

    def fill_conclusion(self, conclusion):
        self.conclusion = conclusion
        self.a_heat.dew_level = int(conclusion.ATower_DewLevel)
        self.a_heat.heat_reduce = int(conclusion.ATower_HeatReduce)
        self.a_heat.dew_point = int(conclusion.ATower_DewPoint)
        self.b_heat.dew_level = int(conclusion.BTower_DewLevel)
        self.b_heat.heat_reduce = int(conclusion.BTower_HeatReduce)
        self.b_heat.dew_point = int(conclusion.BTower_DewPoint)

    @staticmethod
    def time_from_real(real) -> Tuple[int, int, int]:
        return int(real.Load_Rate), int(real.RUN_Time), int(real.RunTime_Rate)

    @property
    def is_a_work(self) -> bool:
        return self._is_a_work

    @is_a_work.setter
    def is_a_work(self, value: bool):
        self._is_a_work = value

    @property
    def is_b_work(self) -> bool:
        return not self._is_a_work

    @property
    def is_a_refresh(self) -> bool:
        return not self.is_a_work

    @property
    def is_b_refresh(self) -> bool:
        return self._is_a_work

    @property
    def work_dew_sum(self) -> SumEntity:
        return self.a_dew_sum if self._is_a_work else self.b_dew_sum

    @work_dew_sum.setter
    def work_dew_sum(self, value: SumEntity):
        if self._is_a_work:
            self.a_dew_sum = value
        else:
            self.b_dew_sum = value

    @property
    def work_heat(self):
        return self.a_heat if self._is_a_work else self.b_heat

    @work_heat.setter
    def work_heat(self, value: TowerHeatEntity):
        if self._is_a_work:
            self.a_heat = value
        else:
            self.b_heat = value

    @property
    def refresh_heat(self) -> TowerHeatEntity:
        return self.b_heat if self._is_a_work else self.a_heat

    @refresh_heat.setter
    def refresh_heat(self, value: TowerHeatEntity):
        if self._is_a_work:
            self.b_heat = value
        else:
            self.a_heat = value

    @property
    def id(self) -> int:
        return self.conclusion.Id

    @property
    def equip_code(self):
        return f"{self.conclusion.StationID}-{self.conclusion.EquipID}"

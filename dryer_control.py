import time
import traceback
from typing import List

from PySide6.QtCore import QThread

import win_config
from biz.heat_biz import threshold_by_name
from entities.app_share_model import AppShareModel
from entities.config_switch import ConfigSwitch
from entities.detail_model import DetailModel
from entities.dryer_entity import DryerEntity, SumEntity, TowerHeatEntity
from time_log import time_log
from utils.config_sql_item import sql_executor
from utils.py_common_utils import add_minute


class DryerControl(QThread):
    def __init__(self, app_share: AppShareModel):
        super().__init__(app_share.parent())
        self._config = win_config.read_json()
        self._app_share = app_share
        self._switch = ConfigSwitch.from_config(self._config['switch'])
        self._instruments: List[DryerEntity] = []
        rows = sql_executor.fetch_all("AdsorptionDryer_Conclusion_sel_all")
        for row in rows:
            item = DryerEntity()
            item.fill_conclusion(row)
            self._instruments.append(item)
            detail = DetailModel(self.parent(), item)
            app_share.detail_models2.append(detail)

    def run(self) -> None:
        while self._app_share.stopped is False:
            self.process()

    def process(self):
        time_log(f"process instruments count {len(self._instruments)}")
        for item in self._app_share.detail_models2:
            if self._app_share.stopped:
                time_log(f"{item.code} got self._app_share.stopped")
                break
            try:
                self.process_each(item.my_entity())
                item.myNotified.emit()
            except:
                traceback.print_exc()
        time.sleep(self._switch.sleep_seconds)

    def process_each(self, item: DryerEntity):
        real = self.get_real(item.conclusion)
        if real is None:
            time_log(f"{item.equip_code} NULL_REAL record")
            return
        station_real = self.get_station_real(item.conclusion)
        if station_real is None:
            time_log(f"{item.equip_code} NULL_station_real record")
            return
        self.put_real(item, real, station_real)
        self.control_switch(item)
        if not item.auto_control or not item.real_run:
            item.time_elapse = item.time_from_real(real)
            item.previous_elapse = (0, 0, 0)
            return
        time_elapse = item.time_from_real(real)
        if time_elapse == (0, 0, 0):
            time_log(f"""{item.equip_code} absolute 0 time elapse.
exit for avoid misjudge initial state""")
            return
        tower_switch = time_elapse[0] < item.time_elapse[0] or item.is_initial
        if tower_switch:
            item.previous_elapse = item.time_elapse
            item.time_elapse = time_elapse
            self.reset_dryer(item)
        else:
            item.time_elapse = time_elapse
            self.sum_work_dew(item)
            self.sum_env_temp(item)
            self.heat_reduce_begin(item)
            self.heat_reduce_end(item)
            self.regenerate_begin(item)

    def control_switch(self, item: DryerEntity):
        auto_control = DryerControl.is_auto_control(item.id)
        if auto_control != item.auto_control:
            if not item.is_initial:
                flag = "1" if auto_control else "0"
                self.insert_control2(item.conclusion, flag, "0", "0")
            item.auto_control = auto_control

    def sum_env_temp(self, item: DryerEntity):
        if self._switch.env_begin < item.time_elapse < self._switch.env_end:
            # 1.1 吸附塔工作后对应3~4小时之间的环境温度平均值
            real = item.real_station
            if item.dew_temp_sum.add(real.Air_T, real.Id):
                time_log(f"{item.equip_code} dew_temp_sum.added {real.Air_T}-{real.Id}")
        elif self._switch.env_end <= item.time_elapse and not item.dew_temp_sum.sync_db:
            if not item.dew_temp_sum.valid:
                item.dew_temp_sum.sync_db = True
                time_log(f"{item.equip_code} dew_temp_sum.invalid {item.dew_temp_sum.count}")
                return
            thresh = threshold_by_name("干燥机露点温度控制点温差")
            item.conclusion.DewPoint = item.dew_temp_sum.avg - float(thresh)
            sql_executor.execute("AdsorptionDryer_Conclusion_update_DewPoint",
                                 item.conclusion.DewPoint, item.id)
            item.dew_temp_sum.sync_db = True
            if self.dew_outside_thresh(item):
                time_log(f"{item.equip_code} DewPoint {item.conclusion.DewPoint} outside_thresh")

    def sum_work_dew(self, item):
        real = item.real
        if self._switch.single_begin < item.time_elapse < self._switch.single_end:
            # 2.1 吸附塔单独工作后5分钟内压缩空气平均露点温度
            if item.work_dew_sum.add(real.CDyer_DewPoint, real.Id):
                time_log(f"{item.equip_code} work_dew_sum.added {real.CDyer_DewPoint}-{real.Id}")
        elif self._switch.single_end <= item.time_elapse and not item.work_dew_sum.sync_db:
            heat = item.work_heat
            if not item.work_dew_sum.valid:
                item.work_dew_sum.sync_db = True
                time_log(f"{item.equip_code} work_dew_sum.invalid {item.work_dew_sum.count}")
                return
            heat.dew_point = item.work_dew_sum.avg
            updated = False
            if heat.heat_reduce <= 0:
                heat.dew_level = heat.dew_point
                heat.heat_reduce = 5
                updated = True
                time_log(f"{item.equip_code} heat_reduce init_dew_level:{heat.dew_level}")
            else:
                loss = heat.dew_point - heat.dew_level
                thresh = float(threshold_by_name("干燥机露点节能提高阈值"))
                limit = 0.1
                if loss < thresh - limit and heat.heat_reduce < self._switch.max_reduce:
                    heat.heat_reduce += 5
                    updated = True
                    time_log(
                        f"{item.equip_code} heat_reduce increased to {heat.heat_reduce} for {loss}={heat.dew_point}-{heat.dew_level}")
                elif loss > thresh + limit:
                    heat.heat_reduce -= 5
                    updated = True
                    time_log(
                        f"{item.equip_code} heat_reduce decreased to {heat.heat_reduce} for {loss}={heat.dew_point}-{heat.dew_level}")
            if updated:
                sql_key = "AdsorptionDryer_Conclusion_update_ATower" if item.is_a_work else \
                    "AdsorptionDryer_Conclusion_update_BTower"
                sql_executor.execute(sql_key, heat.dew_level, heat.heat_reduce, heat.dew_point, item.id)
            else:
                time_log(
                    f"{item.equip_code} heat_reduce unchanged {heat.heat_reduce} for loss={heat.dew_point}-{heat.dew_level}")
            item.work_dew_sum.sync_db = True

    @staticmethod
    def put_real(item: DryerEntity, real, station_real):
        item.previous = None
        if item.real is None or item.real.Id < real.Id:
            item.previous = item.real
            item.real = real
            # 0：A塔干燥B塔再生；1：B塔干燥A塔再生
            item.is_a_work = int(real.Inlet_Q) == 0
        item.prev_station = None
        if item.real_station is None or item.real_station.Id != station_real.Id:
            item.prev_station = item.real_station
            item.real_station = station_real
        item.oldest = DryerControl.get_oldest(item.conclusion)

    def reset_dryer(self, item: DryerEntity):
        item.previous = None
        if item.switch_count >= self._switch.max_switch:
            item.switch_count = 1
            item.a_dew_sum = SumEntity()
            item.b_dew_sum = SumEntity()
            item.a_heat = TowerHeatEntity()
            item.b_heat = TowerHeatEntity()
        else:
            item.switch_count += 1
            item.work_dew_sum = SumEntity()
            item.work_heat.reset()
        item.dew_temp_sum = SumEntity()
        item.regen_begin_id = 0
        item.regen_end_id = 0
        item.init_control_id = self.insert_control(item.conclusion, "0", "0")

    @staticmethod
    def get_real(conclusion):
        return sql_executor.fetch_one("Dryer_Real_latest", conclusion.EquipID, conclusion.StationID)

    @staticmethod
    def get_oldest(conclusion):
        return sql_executor.fetch_one("Dryer_Real_oldest", conclusion.EquipID, conclusion.StationID)

    @staticmethod
    def get_station_real(conclusion):
        return sql_executor.fetch_one("Station_Real_latest", conclusion.StationID)

    def is_quit(self) -> bool:
        return self._app_share.stopped is False

    @staticmethod
    def insert_control(conclusion, heater, regen) -> int:
        return DryerControl.insert_control2(conclusion, "1", heater, regen)

    @staticmethod
    def insert_control2(conclusion, dew, heater, regen) -> int:
        time_log(f"insert_control {conclusion.FactoryID}-{conclusion.StationID}-{conclusion.EquipID} " +
                 f"dew:{dew}-heater:{heater}-regen:{regen}")
        return sql_executor.fetch_val("OPC_DryerSend_insert",
                                      conclusion.FactoryID, conclusion.StationID, conclusion.EquipID,
                                      dew, heater, regen)

    @staticmethod
    def is_auto_control(_id):
        row = sql_executor.fetch_one("AdsorptionDryer_Conclusion_sel_by_id", _id)
        if row is None:
            return False
        return int(row.Auto_Control) == 1

    @staticmethod
    def dew_outside_thresh(item: DryerEntity) -> bool:
        thresh_high = threshold_by_name("干燥机露点温度控制点上限")
        thresh_low = threshold_by_name("干燥机露点温度控制点下限")
        return item.conclusion.DewPoint >= thresh_high or item.conclusion.DewPoint <= thresh_low

    def regenerate_begin(self, item: DryerEntity):
        if not item.real_run:
            return
        if item.step != 12:
            return
        if self.dew_outside_thresh(item):
            return
        if item.regen_begin_id > 0:
            return
        if not (self._switch.dew_begin < item.time_elapse < self._switch.dew_end):
            return
        thresh_dew = threshold_by_name("干燥机露点温度再生切换阈值")
        if item.real.CDyer_DewPoint >= item.conclusion.DewPoint or \
                item.real.CDyer_DewPoint >= thresh_dew:
            # Regeneration_Control
            item.conclusion.Regeneration_Control = 1
            self.conclusion_update_control(item.conclusion)
            item.regen_begin_id = self.insert_control(item.conclusion, None, "1")

    def regenerate_end(self, item: DryerEntity):
        if item.regen_begin_id > 0 and item.regen_end_id <= 0:
            row = sql_executor.fetch_one("OPC_DryerSend_sel_by_id", item.regen_begin_id)
            if row is not None and row.IsSend == "1":
                item.conclusion.Regeneration_Control = 0
                self.conclusion_update_control(item.conclusion)
                item.regen_end_id = self.insert_control(item.conclusion, None, "0")

    @staticmethod
    def conclusion_update_control(conclusion):
        sql_executor.execute("AdsorptionDryer_Conclusion_update_Control",
                             conclusion.Heater_Control, conclusion.Regeneration_Control, conclusion.Id)

    def heat_reduce_begin(self, item: DryerEntity):
        heat = item.refresh_heat
        if heat.begin_id > 0:
            return
        if heat.heat_reduce <= 0:
            return
        if not item.real_run:
            return
        if item.step != 5:
            return
        if item.previous_elapse < self._switch.heat_min_round:
            # 上个周期在露点模式下，切换周期＜5小时10分，这个周期不对加热器进行控制
            return
        begin_elapse = add_minute(self._switch.heat_end, -heat.heat_reduce)
        if item.time_elapse < begin_elapse:
            return
        thresh_temp = threshold_by_name("干燥机出口温度阈值")
        if item.real.CDyer_HeatTowerOutT < thresh_temp:
            return
        item.conclusion.Heater_Control = 1
        self.conclusion_update_control(item.conclusion)
        heat.begin_id = self.insert_control(item.conclusion, "1", None)
        heat.begin_elapse = item.time_elapse

    def heat_reduce_end(self, item: DryerEntity):
        heat = item.refresh_heat
        if heat.end_id > 0 or heat.begin_id <= 0:
            return
        thresh_temp = threshold_by_name("干燥机出口温度阈值")
        end_elapse = add_minute(heat.begin_elapse, heat.heat_reduce)
        if item.time_elapse < end_elapse and item.step == 5 and \
                item.real.CDyer_HeatTowerOutT > thresh_temp - 5:
            return
        item.conclusion.Heater_Control = 0
        self.conclusion_update_control(item.conclusion)
        heat.end_id = self.insert_control(item.conclusion, "0", None)

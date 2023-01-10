import os
import time
import traceback
from typing import List

from biz.heat_biz import threshold_by_name
from entities.config_switch import ConfigSwitch
from entities.dryer_entity import DryerEntity, SumEntity, TowerHeatEntity
from time_log import time_log
from utils.config_sql_item import sql_executor
from utils.py_common_utils import add_minute


class DryerControl:
    def __init__(self, config):
        self._config = config
        self._switch = ConfigSwitch.from_config(self._config['switch'])
        self._instruments: List[DryerEntity] = []
        rows = sql_executor.fetch_all("AdsorptionDryer_Conclusion_sel_all")
        for row in rows:
            item = DryerEntity()
            item.fill_conclusion(row)
            self._instruments.append(item)

    def process(self) -> bool:
        if self.is_quit():
            return False
        time_log(f"process instruments count {len(self._instruments)}")
        for item in self._instruments:
            try:
                self.process_each(item)
            except:
                traceback.print_exc()
        time.sleep(self._switch.sleep_seconds)
        return True

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
        time_elapse = item.time_from_real(real)
        tower_switch = time_elapse < item.time_elapse
        item.time_elapse = time_elapse
        if tower_switch:
            self.reset_dryer(item)
        else:
            self.sum_work_dew(item)
            self.sum_env_temp(item)
            self.heat_reduce_begin(item)
            self.heat_reduce_end(item)
            self.regenerate(item)
            # if self._switch.heat_begin < time_elapse < self._switch.heat_end

    def sum_env_temp(self, item: DryerEntity):
        if self._switch.env_begin < item.time_elapse < self._switch.env_end:
            # 1.1 吸附塔工作后对应3~4小时之间的环境温度平均值
            real = item.real_station
            item.dew_temp_sum.add(real.Air_T, real.Id)
        elif self._switch.env_end <= item.time_elapse and not item.dew_temp_sum.sync_db:
            if not item.work_dew_sum.valid:
                item.dew_temp_sum.sync_db = True
                return
            thresh = threshold_by_name("干燥机露点温度控制点温差")
            item.conclusion.DewPoint = item.work_dew_sum.avg - thresh
            sql_executor.execute("AdsorptionDryer_Conclusion_update_DewPoint",
                                 item.conclusion.DewPoint, item.id)
            item.dew_temp_sum.sync_db = True
            if self.dew_outside_thresh(item):
                time_log(f"{item.equip_code} DewPoint {item.conclusion.DewPoint} outside_thresh")

    def sum_work_dew(self, item):
        real = item.real
        if self._switch.single_begin < item.time_elapse < self._switch.single_end:
            # 2.1 吸附塔单独工作后5分钟内压缩空气平均露点温度
            item.work_dew_sum.add(real.CDyer_DewPoint, real.Id)
        elif self._switch.single_end <= item.time_elapse and not item.work_dew_sum.sync_db:
            heat = item.work_heat
            if not item.work_dew_sum.valid:
                item.work_dew_sum.sync_db = True
                return
            heat.dew_point = item.work_dew_sum.avg
            updated = False
            if heat.heat_reduce <= 0:
                heat.dew_level = heat.dew_point
                heat.heat_reduce = 5
                updated = True
            else:
                loss = heat.dew_point - heat.dew_level
                thresh = float(threshold_by_name("干燥机露点节能提高阈值"))
                limit = 0.1
                if loss < thresh - limit:
                    heat.heat_reduce += 5
                    updated = True
                elif loss > thresh + limit:
                    heat.heat_reduce -= 5
                    updated = True
            if updated:
                sql_key = "AdsorptionDryer_Conclusion_update_ATower" if item.is_a_work else \
                    "AdsorptionDryer_Conclusion_update_BTower"
                sql_executor.execute(sql_key, heat.dew_level, heat.heat_reduce, heat.dew_point, item.id)
            item.work_dew_sum.sync_db = True

    @staticmethod
    def put_real(item, real, station_real):
        item.previous = None
        if item.real is None or item.real.Id != real.Id:
            item.previous = item.real
            item.real = real
            # 0：A塔干燥B塔再生；1：B塔干燥A塔再生
            item.is_a_work = int(real.Inlet_Q) == 0
        item.prev_station = None
        if item.real_station is None or item.real_station.Id != station_real.Id:
            item.prev_station = item.real_station
            item.real_station = station_real

    @staticmethod
    def reset_dryer(item: DryerEntity):
        item.previous = None
        item.dew_temp_sum = SumEntity()
        item.regen_begin_id = 0
        item.regen_end_id = 0
        item.work_dew_sum = SumEntity()
        item.work_heat.reset()

    @staticmethod
    def get_real(conclusion):
        return sql_executor.fetch_one("Dryer_Real_latest", conclusion.EquipID, conclusion.StationID)

    @staticmethod
    def get_station_real(conclusion):
        return sql_executor.fetch_one("Station_Real_latest", conclusion.StationID)

    @staticmethod
    def is_quit() -> bool:
        group_root = "group_info"
        if not os.path.exists(group_root):
            os.makedirs(group_root)
        quit_path = os.path.join(group_root, 'quit.request')
        if os.path.exists(quit_path):
            os.remove(quit_path)
            return True
        return False

    @staticmethod
    def insert_control(conclusion, heater, regen) -> int:
        time_log(f"insert_control {conclusion.FactoryID}-{conclusion.StationID}-{conclusion.EquipID} " +
                 f"heater:{heater}-regen:{regen}")
        row = sql_executor.fetch_one("AdsorptionDryer_Conclusion_sel_by_id", conclusion.Id)
        conclusion.Auto_Control = row.Auto_Control
        if int(conclusion.Auto_Control) == 0:
            # by pass submit plc
            return 1
        return sql_executor.fetch_val("OPC_DryerSend_insert",
                                      conclusion.FactoryID, conclusion.StationID, conclusion.EquipID,
                                      heater, regen)

    @staticmethod
    def dew_outside_thresh(item: DryerEntity) -> bool:
        thresh_high = threshold_by_name("干燥机露点温度控制点上限")
        thresh_low = threshold_by_name("干燥机露点温度控制点下限")
        return item.conclusion.DewPoint >= thresh_high or item.conclusion.DewPoint <= thresh_low

    def regenerate(self, item: DryerEntity):
        if self.dew_outside_thresh(item):
            return

        if item.regen_begin_id <= 0 and \
                self._switch.dew_begin < item.time_elapse < self._switch.dew_end and \
                item.real.CDyer_DewPoint >= item.conclusion.DewPoint:
            # Regeneration_Control
            item.conclusion.Regeneration_Control = 1
            self.conclusion_update_control(item.conclusion)
            item.regen_begin_id = self.insert_control(item.conclusion, None, "1")
        if item.regen_begin_id > 0 and item.regen_end_id <= 0:
            row = sql_executor.fetch_one("OPC_DryerSend_sel_by_id", item.regen_begin_id)
            if int(item.conclusion.Auto_Control) == 0 or \
                    (row is not None and row.IsSend == "1"):
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
        if item.time_elapse < self._switch.heat_begin:
            return
        if heat.heat_reduce <= 0:
            return
        item.conclusion.Heater_Control = 1
        self.conclusion_update_control(item.conclusion)
        heat.begin_id = self.insert_control(item.conclusion, "1", None)

    def heat_reduce_end(self, item: DryerEntity):
        heat = item.refresh_heat
        if heat.end_id > 0 or heat.begin_id <= 0:
            return
        end_elapse = add_minute(self._switch.heat_begin, heat.heat_reduce)
        if item.time_elapse < end_elapse:
            return
        item.conclusion.Heater_Control = 0
        self.conclusion_update_control(item.conclusion)
        heat.end_id = self.insert_control(item.conclusion, "0", None)

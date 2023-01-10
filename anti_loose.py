import os
import time
import traceback
import typing
from dataclasses import replace

from biz.group_biz import GroupBiz
from entities.adjustment import Adjustment
from entities.config_switch import ConfigSwitch
from entities.group_entity import GroupEntity
from entities.instrument_entity import InstrumentEntity, InstrumentReal
from utils.py_common_utils import read_json
from utils.config_sql_item import sql_executor
from time_log import time_log, time_err


class AntiLoose:
    def __init__(self, config):
        self._config = config
        self._switch = ConfigSwitch.from_config(self._config['switch'])
        self._instruments: typing.Dict[int, InstrumentEntity] = {}
        self._groups: typing.List[GroupEntity] = []
        self.init_groups()

    def run(self) -> bool:
        """
        process all groups
        :return: whether quit
        """
        for group in self._groups:
            if self.is_quit():
                return False
            if not group.instruments:
                time_err(f"group({group.id}) has empty machines")
                continue
            biz = GroupBiz(group, self._instruments, self._switch, self._config)
            try:
                biz.process()
            except:
                traceback.print_exc()
        time.sleep(self._switch.sleep_seconds)
        return True

    @staticmethod
    def is_quit():
        if not os.path.exists(GroupBiz.group_root):
            os.makedirs(GroupBiz.group_root)
        quit_path = os.path.join(GroupBiz.group_root, 'quit.request')
        if os.path.exists(quit_path):
            os.remove(quit_path)
            return True
        return False

    def init_groups(self):
        for item in self._config['groups']:
            group = GroupEntity.from_config(item)
            json_path = os.path.join(GroupBiz.group_root, f'group.{group.id}.json')
            if os.path.exists(json_path):
                json_group = read_json(json_path)
                group = self.init_from_json(group, json_group)
            else:
                self.instrument_from_config(group)
            for instrument in group.instruments:
                self._instruments[instrument.id] = instrument
            self._groups.append(group)
        for item in self._config["instruments"]:
            instrument = self._instruments[item["id"]]
            instrument.pressure_init = item["pressure_init"]
            self.instrument_from_db(instrument)

    @staticmethod
    def init_from_json(group: GroupEntity, json: typing.Dict):
        group = replace(group, **json)
        group.instruments = []
        if json.get("instruments"):
            for item in json.get("instruments"):
                entity = InstrumentEntity()
                entity = replace(entity, **item)
                real = InstrumentReal()
                entity.real = replace(real, **item["real"])
                if item.get("previous"):
                    previous = InstrumentReal()
                    entity.previous = replace(previous, **item.get("previous"))
                group.instruments.append(entity)
        group.adjustments = []
        if json.get("adjustments"):
            for item in json.get("adjustments"):
                entity = Adjustment()
                entity = replace(entity, **item)
                group.adjustments.append(entity)
        return group

    @staticmethod
    def instrument_from_db(instrument: InstrumentEntity):
        """
        init instrument by id from db
        :param instrument:
        """
        row = sql_executor.fetch_one('BB_Instrument_by_id', instrument.id)
        if not row:
            time_log(f'BB_Instrument_by_id-{instrument.id}-failed')
            return
        if row.Rated_Q:
            instrument.rated_Q = float(row.Rated_Q)
        if row.Rated_A:
            instrument.rated_A = float(row.Rated_A)

    def instrument_from_config(self, group: GroupEntity):
        for _instrument in self._config["instruments"]:
            if _instrument["group_id"] != group.id:
                continue
            instrument = InstrumentEntity()
            instrument = replace(instrument, **_instrument)
            instrument.real = InstrumentReal()
            instrument.previous = InstrumentReal()
            group.instruments.append(instrument)

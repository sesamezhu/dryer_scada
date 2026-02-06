import time
import traceback

from typing import List

from PySide6.QtCore import QObject, Signal, Slot, Property

from dryer_control import DryerControl
from entities.app_share_model import AppShareModel
from entities.detail_model import DetailModel
from time_log import time_log, terminal_restore
from utils.config_sql_item import sql_executor
from utils.py_common_utils import dump_traces


class Backend(QObject):
    myNotified = Signal()

    def __init__(self, _parent):
        super().__init__(_parent)
        self._app_share = AppShareModel(self.parent())
        self._dryer_control = DryerControl(self._app_share)
        self._switch = self._dryer_control.switch

    @Slot()
    def start_threads(self):
        time_log("Backend.started_threads")
        self._dryer_control.start()

    @Slot()
    def stop_threads(self):
        time_log("Backend.stopping_threads")
        self._app_share.stopped = True
        dump_traces()
        time.sleep(0.2)
        while self._dryer_control.isRunning():
            time_log("dryer_control.isRunning")
            time.sleep(0.1)
        try:
            sql_executor.close()
        except:
            traceback.print_exc()
        time_log("Backend.stopped_threads")
        terminal_restore()

    @Property("QVariantList", notify=myNotified)
    def detail_models(self) -> List[DetailModel]:
        return self._app_share.detail_models2

    @Property(int, notify=myNotified)
    def grid_rows(self) -> int:
        return self._switch.grid_rows

    @Property(int, notify=myNotified)
    def grid_columns(self) -> int:
        return self._switch.grid_columns

import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import time_log
import win_config
from dryer_control import DryerControl
from entities.backend_model import Backend
from utils.config_sql_item import sql_executor
from utils.py_common_utils import check_dup_process

sys.path.append('entities')
sys.path.append('utils')
sys.path.append('biz')


if __name__ == '__main__':
    time_log.time_log('main is launched')
    config = win_config.read_json()
    if check_dup_process(config["switch"]["port"]):
        time_log.time_log('duplicate process with same port')
        sys.exit(-1)
    # a = DryerControl(config)
    # if check_dup_process(a._switch.port):
    #     time_log.time_log('duplicate process with same port')
    #     sys.exit(-1)
    # while True:
    #     if not a.process():
    #         break
    # sql_executor.close()
    app = QGuiApplication(sys.argv)
    backend = Backend(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl("resource/main.qml"))
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())

from typing import List, Tuple
import numpy as np
from PySide6.QtCore import QObject, Signal

from entities.detail_model import DetailModel


class AppShareModel(QObject):
    myNotified = Signal()

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self._stopped = False
        self.log_frames: List[Tuple[np.ndarray, str, str]] = []
        self.detail_models2: List[DetailModel] = []

    @property
    def stopped(self) -> bool:
        return self._stopped

    @stopped.setter
    def stopped(self, value: bool):
        self._stopped = value

from utils.config_sql_item import sql_executor


class HeatBiz:
    def __init__(self):
        pass


def threshold_by_name(name: str):
    return sql_executor.fetch_val("Threshold_by_name", name)

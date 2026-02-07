from entities.dryer_entity import DryerEntity
from utils.config_sql_item import sql_executor


def threshold_by_name(name: str) -> float:
    return sql_executor.fetch_val("Threshold_by_name", name)


class HeatBiz:
    @staticmethod
    def threshold(pre, item: DryerEntity) -> float:
        value = threshold_by_name(f"{pre}{item.site_id}{item.sub_id}")
        return value or threshold_by_name(pre)


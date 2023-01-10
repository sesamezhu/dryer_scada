# from entities.instrument_entity import InstrumentReal
# from utils.config_sql_item import sql_executor
#
#
# def to_entity(row, entity: InstrumentReal):
#     entity.Q = row.Q
#     entity.eQ = row.eQ
#     entity.C = row.C
#
#
# def latest(_id, entity: InstrumentReal):
#     row = sql_executor.fetch_one('', _id)
#     if row:
#         to_entity(row, entity)
#
#
# def previous(_id, entity: InstrumentReal):
#     row = sql_executor.fetch_one('', _id)
#     if row:
#         to_entity(row, entity)

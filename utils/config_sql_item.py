import json
import random
import time
import traceback
from typing import List

from time_log import time_log, time_err
import pyodbc
import multiprocessing

json_sql_path = "configs/sql.json"
json_config_path = "configs/config.json"
CONN_POOL_LEN = 1
CONN_MAX_COUNT = 128


def read_sql_json():
    with open(json_sql_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class ConfigSqlItem:
    def __init__(self):
        self.id = ""
        self.sql = ""


class OdbcConnItem:
    def __init__(self, conn: str):
        time_log(conn[:-20])
        self.conn = pyodbc.connect(conn, autocommit=True)
        self.cursor = self.conn.cursor()
        self.committing = False
        self.count = random.randint(0, CONN_MAX_COUNT // 16)


def read_config_conn():
    with open(json_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['switch']['conn']


class SqlOperation:
    def __init__(self) -> None:
        self._locker = multiprocessing.Lock()
        self._str_sql = read_sql_json()
        self._config_conn = read_config_conn()
        self._conns: List[OdbcConnItem] = []
        for i in range(CONN_POOL_LEN):
            self._conns.append(OdbcConnItem(self._config_conn))
        self._number = 0
        self.sqls: {str: str} = {}
        for item in self._str_sql["sqls"]:
            self.sqls[item["id"]] = " ".join(item["sql"])

    def acquire_conn(self) -> OdbcConnItem:
        retry_times = 0
        while True:
            with self._locker:
                if not self._conns:
                    return None
                for i in range(CONN_POOL_LEN):
                    self._number += 1
                    if self._number >= CONN_POOL_LEN:
                        self._number = 0
                    conn = self._conns[self._number]
                    if not conn.committing:
                        if conn.count >= CONN_MAX_COUNT:
                            try:
                                conn.conn.close()
                            except:
                                traceback.print_exc()
                            conn = OdbcConnItem(self._config_conn)
                            self._conns[self._number] = conn
                        conn.committing = True
                        return conn
            retry_times += 1
            time_err(f"failed to acquire conn from pool: {retry_times}")
            if retry_times > 6:
                return None
            time.sleep(0.03)

    def release_conn(self, conn):
        with self._locker:
            conn.committing = False

    def execute(self, key, *params):
        time_log(f"sql_executing:{key} {params}")
        return self.do_execute("execute", key, params)

    def do_execute(self, _type, key, params):
        conn = self.acquire_conn()
        if conn is None:
            time_log(f"GOT NULL CONNECTION:{key} {params}")
            return None
        try:
            return self.invoke(_type, conn.cursor, key, params)
        except BaseException as err:
            traceback.print_exc()
            conn.count += 1
            raise err
        finally:
            self.release_conn(conn)

    def invoke(self, _type, cursor, key, params):
        if _type == "execute":
            cursor.execute(self.sqls[key], params)
            cursor.commit()
            return None
        elif _type == "fetch_all":
            cursor.execute(self.sqls[key], params)
            return cursor.fetchall()
        elif _type == "fetch_one":
            cursor.execute(self.sqls[key], params)
            return cursor.fetchone()
        elif _type == "fetch_val":
            cursor.execute(self.sqls[key], params)
            return cursor.fetchval()

    def fetch_all(self, key, *params):
        return self.do_execute("fetch_all", key, params)

    def fetch_one(self, key, *params):
        return self.do_execute("fetch_one", key, params)

    def fetch_val(self, key, *params):
        return self.do_execute("fetch_val", key, params)

    def close(self):
        while self._conns:
            time_log("closing no {}".format(len(self._conns)))
            with self._locker:
                if not self._conns[-1].committing:
                    odbc = self._conns.pop()
                    try:
                        odbc.conn.close()
                    except:
                        traceback.print_exc()


sql_executor = SqlOperation()

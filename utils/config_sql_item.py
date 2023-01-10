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
CONN_MAX_COUNT = 128000


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

    def acquire_cursor(self):
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
                        # sys.stdout.write("acquire conn.no {}\n".format(self._number))
                        conn.committing = True
                        return conn.cursor
            retry_times += 1
            time_err(f"failed to acquire conn from pool: {retry_times}")
            if retry_times > 6:
                return None
            time.sleep(0.03)

    def release_cursor(self, cursor):
        conn: OdbcConnItem = None
        with self._locker:
            for item in self._conns:
                if item.cursor == cursor:
                    item.count += 1
                    if item.count > CONN_MAX_COUNT:
                        conn = item
                    else:
                        item.committing = False
                    break
        if conn is not None:
            # replace conn with a new
            with self._locker:
                self._conns.remove(conn)
            try:
                conn.conn.close()
            except:
                traceback.print_exc()
            try:
                conn = OdbcConnItem(self._str_sql["conn"])
            except:
                traceback.print_exc()
            with self._locker:
                self._conns.append(conn)

    def execute(self, key, *params):
        time_log(f"sql_execute:{key} { params}")
        cursor = self.acquire_cursor()
        try:
            cursor.execute(self.sqls[key], params)
            cursor.commit()
        finally:
            self.release_cursor(cursor)

    def fetch_all(self, key, *params):
        cursor = self.acquire_cursor()
        try:
            cursor.execute(self.sqls[key], params)
            return cursor.fetchall()
        finally:
            self.release_cursor(cursor)

    def fetch_one(self, key, *params):
        cursor = self.acquire_cursor()
        try:
            cursor.execute(self.sqls[key], params)
            return cursor.fetchone()
        finally:
            self.release_cursor(cursor)

    def fetch_val(self, key, *params):
        cursor = self.acquire_cursor()
        try:
            cursor.execute(self.sqls[key], params)
            return cursor.fetchval()
        finally:
            self.release_cursor(cursor)

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

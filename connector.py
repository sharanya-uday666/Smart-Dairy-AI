import os
import sqlite3

DB_PATH = os.path.join(os.getcwd(), "smart_dairy.db")

# --- GLOBAL SQLITE CURSOR PATCH ---
# Intercepts direct sqlite3 connections to support dictionary=True and %s placeholders
if not hasattr(sqlite3.Connection, "_original_cursor"):
    _original_sqlite_cursor = sqlite3.Connection.cursor
    sqlite3.Connection._original_cursor = _original_sqlite_cursor

    class DictCursorWrapper:
        def __init__(self, cursor):
            self.cursor = cursor
        def execute(self, operation, params=None, multi=False):
            if params:
                operation = operation.replace("%s", "?")
                return self.cursor.execute(operation, params)
            return self.cursor.execute(operation)
        def executemany(self, operation, seq_params):
            operation = operation.replace("%s", "?")
            return self.cursor.executemany(operation, seq_params)
        def fetchone(self):
            row = self.cursor.fetchone()
            if row is None: return None
            return dict(row) if isinstance(row, sqlite3.Row) else row
        def fetchall(self):
            rows = self.cursor.fetchall()
            if not rows: return []
            return [dict(r) if isinstance(r, sqlite3.Row) else r for r in rows]
        def fetchmany(self, size=None):
            rows = self.cursor.fetchmany(size) if size is not None else self.cursor.fetchmany()
            if not rows: return []
            return [dict(r) if isinstance(r, sqlite3.Row) else r for r in rows]
        @property
        def lastrowid(self): return self.cursor.lastrowid
        @property
        def rowcount(self): return self.cursor.rowcount
        def close(self): return self.cursor.close()
        def __iter__(self):
            for row in self.cursor:
                yield dict(row) if isinstance(row, sqlite3.Row) else row
        def __enter__(self): return self
        def __exit__(self, et, ev, tb): self.close()

    def _patched_cursor(self, *args, **kwargs):
        dictionary = kwargs.pop('dictionary', False)
        kwargs.pop('buffered', None)
        kwargs.pop('named_tuple', None)
        if dictionary and self.row_factory is None:
            self.row_factory = sqlite3.Row
        cursor = self._original_cursor(*args, **kwargs)
        if dictionary:
            return DictCursorWrapper(cursor)
        return cursor

    sqlite3.Connection.cursor = _patched_cursor

class CursorProxy:
    def __init__(self, cursor, dictionary=False):
        self.cursor = cursor
        self.dictionary = dictionary

    def execute(self, operation, params=None, multi=False):
        if params:
            operation = operation.replace("%s", "?")
            return self.cursor.execute(operation, params)
        return self.cursor.execute(operation)

    def executemany(self, operation, seq_params):
        operation = operation.replace("%s", "?")
        return self.cursor.executemany(operation, seq_params)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None: return None
        return dict(row) if self.dictionary else row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows: return []
        return [dict(r) for r in rows] if self.dictionary else rows

    def fetchmany(self, size=None):
        rows = self.cursor.fetchmany(size) if size is not None else self.cursor.fetchmany()
        if not rows: return []
        return [dict(r) for r in rows] if self.dictionary else rows

    @property
    def lastrowid(self): return self.cursor.lastrowid
    @property
    def rowcount(self): return self.cursor.rowcount
    def close(self): return self.cursor.close()
    def __iter__(self):
        for row in self.cursor:
            yield dict(row) if self.dictionary else row

class ConnectionProxy:
    def __init__(self, conn): self.conn = conn

    def cursor(self, *args, **kwargs):
        dictionary = kwargs.get('dictionary', False)
        return CursorProxy(self.conn.cursor(), dictionary=dictionary)

    def commit(self): return self.conn.commit()
    def rollback(self): return self.conn.rollback()
    def close(self): return self.conn.close()
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        if et: self.rollback()
        else: self.commit()
        self.close()

def connect(*args, **kwargs):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return ConnectionProxy(conn)

Error = sqlite3.Error
IntegrityError = sqlite3.IntegrityError
DatabaseError = sqlite3.DatabaseError
ProgrammingError = sqlite3.ProgrammingError

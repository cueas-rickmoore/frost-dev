
import datetime
import os
import sqlite3

from atmosci.utils.options import stringToTuple

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SANITY_CHECK = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='_constraints_'"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def formatForSql(value):
    if hasattr(value, 'dtype'):
        if value.dtype.kind == 'i': return '%d' % value
        elif value.dtype.kind == 'S': return '"%s"' % value
        elif value.dtype.kind == 'f': return str(value)
    elif isinstance(value, (int,long)): return '%d' % value
    elif isinstance(value, basestring): return '"%s"' % value
    elif isinstance(value, float): return str(value)
    else: return str(value)

def guessType(value):
    if isinstance(value, int): return int
    elif isinstance(value, float): return float
    elif isinstance(value, basestring):
        if value.isdigit(): return int
        # possible float ?
        try: return float(value)
        except: pass
    return 'object'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SqliteRowIterator(object):

    def __init__(self, manager, sql, result_type='row',
                       disconnect_on_stop=False):
        self.manager = manager
        self.cursor = manager.connection_cursor
        self.cursor.execute(sql)
        self.disconnect_on_stop = disconnect_on_stop
        self.result_type = result_type

    def __iter__(self):
        return self

    def next(self):
        if self.cursor is not None:
            row = self.cursor.fetchone()
            if row is not None:
                if self.result_type in (dict,'dict'):
                    if isinstance(row, sqlite3.Row):
                        return dict(zip(row.keys(), row))
                    else:
                        dict_ = { }
                        for indx, column in enumerate(self.cursor.description):
                            dict_[column[0]] = row[indx]
                        return dict_
                else: return row
            else:
                self.cursor = None
                if self.disconnect_on_stop:
                    self.manager.disconnect()
                    del self.manager
                raise StopIteration
        else:
            #manager.connection.row_factory = self.old_row_factory
            raise IndexError, 'The iterator is no longer viable'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SqliteDatabaseManager(object):

    AUTO_COMMITABLE = ('DELETE', 'INSERT', 'UPDATE')

    def __init__(self, database_filepath, auto_commit=True, commit_rate=100,
                       return_text_type=unicode, row_factory=None):
        self.commit_rate = commit_rate
        self.auto_commit = auto_commit
        self.return_text_type = return_text_type
        if row_factory == 'row': self.row_factory = sqlite3.Row
        else: self.row_factory = row_factory

        self.db_filepath = None
        self.connection = None
        self.connection_cursor = None
        self.num_pending_transactions = 0

        db_filepath = os.path.normpath(os.path.abspath(database_filepath))
        self.connect(db_filepath)

        self._sanityCheck()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initialize(self, table_defs, index_defs=None, unique_index_defs=None):
        if os.path.exists(self.db_filepath):
            self.disconnect()
            os.remove(self.db_filepath)
            self.connect()

        # initialize the constraints table
        self.createTable('_constraints_',
                         ( ('table_name', 'TEXT'), ('columns', 'TEXT') ),
                         'UNIQUE (table_name)')

        # inititialize the rest of the tables
        self.createTables(table_defs)

        # initialize indexes on the tables
        if index_defs is not None:
            self.createIndexes(index_defs)
        if unique_index_defs is not None:
            self.createIndexes(unique_index_defs, unique=True)

        # cache the lists of tables, columns and constraints
        self._sanityCheck()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createIndexes(self, index_defs, unique=False):
        for index_def in index_defs:
            self.createIndex(*index_def, unique=unique)

    def createIndex(self, index_name, table_name, columns=None, unique=False):
        if unique: tmpl = "CREATE UNIQUE INDEX %s ON %s(%s)" 
        else: tmpl = "CREATE INDEX %s ON %s(%s)"
        if columns is not None:
            if isinstance(columns, (list,tuple)):
                sql = tmpl % (index_name, table_name, ','.join(columns))
            elif isinstance(columns, basestring):
                sql = tmpl % (index_name, table_name, columns)
            else:
                msg = "Invalid type for columns argument : %s"
                raise TypeError, msg % type(columns)
        else:
            sql = tmpl % (index_name, table_name, index_name)
        self.execute(sql)
        self.commit()
        self.indexes = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createTables(self, table_defs):
        for table_def in table_defs:
            self.createTable(*table_def)

    def createTable(self, table_name, column_defs, constraints=None):
        ERRMSG = 'Invalid column defintion at item %d in %d table'
        CT = "CREATE TABLE %s(%s)"
        FK = "FOREIGN KEY(%s) REFERENCES %s(%s)"
        column_names = [ ]
        columns = [ ]
        foreign = [ ]
        other = [ ]
        for indx, definition in enumerate(column_defs):
            if isinstance(definition, basestring):
                other.append(definition)
            elif isinstance(definition, tuple):
                if len(definition) == 2:
                    columns.append('%s %s' % definition)
                elif len(definition) == 3:
                    columns.append('%s %s' % definition[:2])
                    foreign.append(FK % (definition[0], definition[2][0],
                                         definition[2][1]))
                else: raise ValueError, ERRMSG % (indx+1, table_name)
                column_names.append(definition[0])
            else: raise TypeError, ERRMSG % (indx+1, table_name)

        table_def = ', '.join(columns)
        if other: table_def = '%s, %s' % (table_def, ', '.join(other))
        if foreign: table_def = '%s, %s' % (table_def, ', '.join(foreign))

        _constraints_ = [ ]
        if isinstance(constraints, basestring):
            table_def = '%s, %s' % (table_def, constraints)
            if 'UNIQUE' in constraints:
                unique = stringToList(constraints[constraints.find('('):].strip())
                _constraints_.append(unique) 
            else:  _constraints_.append(constraints) 

        elif isinstance(constraints, (tuple,list)):
            for constraint in constraints:
                table_def = '%s, %s' % (table_def, constraint)
                if 'UNIQUE' in constraint:
                    unique = stringToList(constraint[constraint.find('('):])
                else: self.addConstraint(table_name, constraint)

        sql = CT % (table_name, table_def)
        self.execute(sql)
        self.commit()

        if _constraints_:
            for columns in _constraints_:
                self._insert('_constraints_', (table_name, ','.join(columns)))
            self.commit()

        self.listColumns(table_name)
        self.tables = None

    def addConstraint(self, table_name, *columns):
        return self._insert('_constraints_', (table_name, ','.join(columns)))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addRecord(self, table_name, column_data, fill_with_missing=False):
        column_names = self.listColumns(table_name)
        if column_names is None:
            raise ValueError, "No table named '%s' in database" % table_name

        elif isinstance(column_data, (tuple,list)):
            return self._insert(table_name, column_data)

        elif isinstance(column_data, dict):
            for column_name in column_names:
                if column_name not in column_data and fill_with_missing:
                    missing_value = self._missingValue(table_name, column_name)
                    column_data[column_name] = missing_value
            return self._insert(table_name, column_data)

        else:
            errmsg = "Invalid type for 'column_data' argument : %s"
            raise TypeError, errmsg % type(column_data)

    def updateRecord(self, table_name, column_data, constraints):
        where = self._constrain(table_name, column_data, constraints)
        self._update(table_name, column_data, where)

    def addOrUpdate(self, table_name, column_data, constraints=None,
                          fill_with_missing=False):
        # check for existing record and update if found
        where = self._constrain(table_name, column_data, constraints)
        if self._recordExists(table_name, where):
            self.updateRecord(table_name, column_data, where)
        # no existing record, add one
        else: self.addRecord(table_name, column_data, fill_with_missing)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteRecord(self, table_name, constraints):
        DEL = "DELETE FROM %s %s"
        sql = DEL % (table_name, self._parseConstraints(constraints))
        self.execute(sql)
        self.commit()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, table_name, column_names, constraints=None, 
                      result_type='dict', fetch='all'):
        if isinstance(column_names, basestring):
            if column_names in ('*','all'): columns_ = '*'
            else: columns_ = (column_names,)
        elif isinstance(column_names, (tuple,list)):
            columns_ = tuple(column_names)
        else:
            errmsg = "Unsupported type for 'column_names' argument: %s"
            raise TypeError, errmsg % type(column_names)

        if constraints is not None:
            where = self._parseConstraints(constraints)
            return self._select(table_name, columns_, where, fetch,
                                result_type)
        else:
            return self._select(table_name, columns_, None, fetch,
                                result_type)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateColumn(self, table_name, column_name, new_value, constraints,
                           commit=True):
        UPC = "UPDATE %s SET %s=%s %s"
        sql = UPC % (table_name, column_name, formatForSql(new_value),
                     self._parseConstraints(constraints))
        if commit:
            self.execute(sql)
            self.commit()
        else: self.autoexec(sql)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def columnExists(self, table_name, column_name):
        return column_name in self.listColumns()

    def indexExists(self, index_name):
        return index_name in self.listIndexes()

    def listColumns(self, table_name):
        if self.columns is None: self.columns = { }
        if table_name not in self.columns:
            result = self.fetch("PRAGMA TABLE_INFO(%s)" % table_name)
            self.columns[table_name] = tuple([column[1] for column in result])
        return self.columns[table_name]

    def listIndexes(self):
        if self.indexes is None: self._refreshIndexList()
        return self.indexes

    def listTables(self):
        if self.tables is None: self._refreshTableList()
        return self.tables

    def numRecords(self, table_name, constraints=None):
        if constraints is not None:
            where = self._parseConstraints(constraints)
            sql = 'SELECT COUNT(ucanid) FROM %s %s' % (table_name, where)
        else: sql = 'SELECT COUNT(ucanid) FROM %s' % table_name
        return self.fetch(sql)[0][0]

    def recordExists(self, table_name, constraints):
        TEST = 'SELECT EXISTS(SELECT 1 FROM %s %s LIMIT 1)'
        where = self._parseConstraints(constraints)
        sql = TEST % (table_name, where)
        return  self.fetch(sql)[0][0]

    def tableExists(self, table_name):
        return table_name in self.listTables()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def autoexec(self, sql, values=None):
        result = self.execute(sql, values)
        if not self.auto_commit:
            return result
        blank = sql.find(' ')
        if sql[:blank] in self.AUTO_COMMITABLE:
            self.num_pending_transactions += 1
            if self.num_pending_transactions >= self.commit_rate:
                self.commit()
        elif sql[:blank] not in ('SELECT','PRAGMA'):
            errmsg = "'%s' SQL statement is not supported for auto commit."
            raise SyntaxError, errmsg % sql[:blank]
        return result

    def closeConnection(self):
        if self.connection is not None:
            if self.num_pending_transactions > 0:
                self.connection.commit()
            self.connection.close()
            self.connection = None
            self.connection_cursor = None
        # closed connections cannot have tables
        self.columns = { }
        self.indexes = None
        self.tables = None
        self.table_constraints = { }

    disconnect = closeConnection

    def closeCursor(self):
        self.connection_cursor.close()
        self.connection_cursor = None

    def commit(self):
        self.connection.commit()
        self.num_pending_transactions = 0

    def connect(self, database_filepath=None, return_text_type=None,
                      row_factory=None):
        if return_text_type is not None:
            self.return_text_type = return_text_type
        if row_factory is not None:
            self.row_factory = row_factory

        self.closeConnection()

        if database_filepath is not None:
            db_filepath = os.path.normpath(os.path.abspath(database_filepath))
        else:
            db_filepath = self.db_filepath
        self.db_filepath = db_filepath

        self.connection = sqlite3.connect(db_filepath)

        if self.return_text_type in ('optimize', 'optimized'):
            self.connection.text_factory = sqlite3.OptimizedUnicode
        elif self.return_text_type in (str, 'acii', 'utf-8'):
            self.connection.text_factory = str

        if self.row_factory is not None:
            self.connection.row_factory = self.row_factory

        self.connection_cursor = self.connection.cursor()

        self._sanityCheck()

    def cursor(self):
        if self.connection is None: self.connect()
        if self.connection_cursor is None:
            self.connection_cursor = self.connection.cursor()
        return self.connection_cursor

    def execute(self, sql, values=None):
        cursor = self.cursor()
        if values is None:
            try:
                return cursor.execute(sql)
            except Exception as e:
                e.args = ('ERROR in SQL : %s' % sql,) + e.args
                raise e
        else:
            try:
                return cursor.execute(sql, values)
            except Exception as e:
                e.args = ('ERROR in SQL : %s' % sql,
                          'Values = %s' % str(values),) + e.args
                raise e

    def fetch(self, sql, how_many=None):
        cursor = self.cursor()
        if isinstance(how_many, int):
            results = cursor.execute(sql).fetchmany(how_many)
            if how_many == 1: return results[0]
            else: return results
        else: return cursor.execute(sql).fetchall()

    def iterator(self, sql):
        return SqliteRowIterator(self, sql)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _columnNamesFromHint(self, columns_hint):
        if isinstance(columns_hint, basestring):
            if columns_hint in self.listTables():
                return tuple(self.listColumns(columns_hint))
            else: return (columns_hint,)
        elif isinstance(columns_hint, (tuple,list)):
            return tuple(columns_hint)
        elif isinstance(columns_hint, sqlite3.Cursor):
            return tuple([column[0] for column in columns_hint.description])
        else:
            errmsg = "Invalid type of 'columns_hint' argument : %s"
            raise TypeError, errmsg % type(columns_hint)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _constrain(self, table_name, constraints=None, column_data=None):
        if constraints is not None:
            return self._parseConstraints(constraints)
        elif column_data is not None:
            _constraints_ = self._hardConstraints(table_name, column_data)
            if _constraints_ is not None:
                return self._parseConstraints(_constraints_)
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _deserialize(self, table_name, row):
        return row

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _hardConstraints(self, table_name, column_data):
        if table_name in self.table_constraints:
            is_dict = isinstance(column_data, dict)
            if not is_dict:
                column_names = self.listColumns(table_name)
                if isinstance(column_data, basestring):
                    column_data = [column.strip()
                                   for column in column_data.split(',')]
            constraints = [ ]
            for column_name in self.table_constraints[table_name]:
                if is_dict: 
                    constraints.append((column_name,column_data[column_name]))
                else:
                    indx = column_names.index(column_name)
                    constraints.append((column_name,column_data[indx]))
            return tuple(constraints)
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _insert(self, table_name, column_data):
        column_names = self.listColumns(table_name)
        if column_names is None:
            raise ValueError, "No table named '%s' in database" % table_name
        num_columns = len(column_names)

        if isinstance(column_data, (tuple,list)):
            num_values = len(column_data)
            if num_values == num_columns:
                qs = ',?' * (num_values -1)
                sql = "INSERT INTO %s VALUES (?%s)" % (table_name, qs)
                return self.execute(sql, column_data)
            else:
                if num_values < num_columns:
                    errmsg = "Only %d values passed, table '%s' has %d columns"
                elif num_values > num_columns:
                    errmsg = "Passed %d values,"
                    errmsg += "but table '%s' has only %d columns."
                errmsg += 'When passing a list/tuple, a value must be'
                errmsg += ' supplied for each column in the table.'
                raise ValueError, errmsg % (num_values, table_name, num_columns)

        elif isinstance(column_data, dict):
            columns = [ ]
            values = [ ]
            for column_name in column_names:
                columns.append(column_name)
                values.append(column_data[column_name])
            qs = ',?' * (len(values) -1)
            columns = ', '.join(columns)
            sql = "INSERT INTO %s(%s) VALUES (?%s)" % (table_name, columns, qs)
            return self.execute(sql, values)

        else:
            errmsg = "Invalid type for 'data' argument : %s"
            raise TypeError, errmsg % type(column_data)

    INSERT = _insert

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _missingValue(self, table_name, column_name):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _parseConstraints(self, constraints):
        if isinstance(constraints, basestring):
            if 'where' in constraints:
                return constraints.replace('where','WHERE')
            elif 'WHERE' in constraints: return constraints
            else: return 'WHERE %s' % constraints

        if isinstance(constraints, (tuple,list)):
            constraints_ = [ ]
            for constraint in constraints:
                if isinstance(constraint, basestring):
                    constraints_.append(constraint)
                elif isinstance(constraint, (tuple,list)):
                    constraint_ = list(constraint)
                    num_terms = len(constraint_)
                    if num_terms == 2:
                        constraint_.insert(1,'=')
                    elif num_terms != 3:
                        errmsg = 'Constraints with %d terms are not supported'
                        raise ValueError, errmsg % num_terms

                    constraint_[2] = formatForSql(constraint_[2])
                    constraints_.append('%s %s %s' % tuple(constraint_))
                else:
                    errmsg = "Invalid type for constraint %d : %s"
                    position = len(constraints_) + 1
                    raise TypeError, errmsg % (position, type(constraint))

            return 'WHERE %s' % ' and '.join(constraints_)

        elif isinstance(constraints, dict):
            constraints_ = [ ]
            for key, value in constraints.items():
                constraints_.append('(%s = %s)' % (key, formatForSql(value)))
            return 'WHERE %s' % ' and '.join(constraints_)

        else:
            errmsg = "Invalid type for 'constraints' argument : %s"
            raise TypeError, errmsg % type(constraints)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _parseTables(self, tables):
        if tables in ('all','*') or tables is None:
            return self.listTables()
        elif isinstance(tables, basestring):
            return stringToTuple(tables)
        elif isinstance(tables, (tuple,list)):
            return tables
        else:
            errmsg = "Invalid type for 'tables' argument : %s"
            raise TypeError, errmsg % type(tables)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _recordExists(self, table_name, where):
        TEST = 'SELECT EXISTS(SELECT 1 FROM %s %s LIMIT 1)'
        sql = TEST % (table_name, where)
        return  self.fetch(sql)[0][0]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _refreshColumnsList(self):
        self.columns = { }
        for table_name in self.tables:
            result = self.fetch("PRAGMA TABLE_INFO(%s)" % table_name)
            self.columns[table_name] = tuple([column[1] for column in result])

    def _refreshIndexList(self):
        sql = "SELECT name FROM sqlite_master WHERE type = 'index'"
        self.indexes = tuple([item[0] for item in self.fetch(sql)])

    def _refreshTableList(self):
        sql = "SELECT name FROM sqlite_master WHERE type = 'table'"
        self.tables = tuple([item[0] for item in self.fetch(sql)])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _restructure(self, result_type, table_name, query_results,
                           columns_hint=None):
        if query_results is None or len(query_results) < 1: return None

        if result_type in (dict,'dict'):
            if isinstance(query_results[0], sqlite3.Row):
                if len(query_results) > 1:
                    collection = [ ]
                    for row in query_results:
                        data_dict = dict(zip(row.keys(), row))
                        collection.append(data_dict)
                    return tuple(collection)
                else:
                    row = query_results[0]
                    return dict(zip(row.keys(), row))

            else:
                column_names = self._columnNamesFromHint(columns_hint)
                if len(query_results) > 1:
                    collection = [ ]
                    for result in query_results:
                        data_dict = dict(zip(column_names, result))
                        collection.append(data_dict)
                    return tuple(collection)
                else:
                    result = query_results[0]
                    return dict(zip(column_names, result))

        elif result_type == 'array':
            import numpy as N
            num_results = len(query_results)

            dtypes = [ ]
            if isinstance(query_results[0], sqlite3.Row):
                row = query_results[0]
                for column in row.keys():
                    dtype = ("'%s'" % column, guessType(row[column]))
                    dtypes.append(dtype)
            else:
                column_names = self._columnNamesFromHint(columns_hint)
                for indx in range(len(column_names)):
                    dtype = ("'%s'" % column_names[indx],
                             guessType(columns[indx]))
                    dtypes.append(dtype)

            records = N.recarray(num_results, dtype=dtypes)
            for indx in range(num_results):
                records[indx] = query_results[indx]
            return records

        else: return query_results

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _sanityCheck(self):
        db_initialized = self.execute(SANITY_CHECK).fetchone()[0]
        if db_initialized:
            sql = "SELECT table_name, columns FROM _constraints_"
            for table_name, columns in self.fetch(sql):
                self.table_constraints[table_name] = tuple(columns.split(','))
            self.listTables()
            for table_name in self.tables:
                self.listColumns(table_name)
            self.listIndexes()
        else:
            self.columns = { }
            self.indexes = None
            self.tables = None
            self.table_constraints = { }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _serialize(self, table_name, row):
        return row

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _select(self, table_name, columns='*', where=None,
                      fetch='all', result_type='row', sort_by=None):

        if isinstance(columns, basestring): _columns = columns
        elif isinstance(columns, (tuple,list)): _columns = ','.join(columns)
        else:
            errmsg = "Invalid type for 'columns' argument : %s"
            raise TypeError, errmsg % type(columns)

        sql = "SELECT %s FROM %s" % (_columns, table_name)
        if where is not None:
            sql = "%s %s" % (sql, where)

        if isinstance(sort_by, basestring):
            if 'ORDER BY' in sort_by:
                sql = '%s %s' % (sql, sort_by)
            elif 'order by' in sort_by:
                sql = '%s %s' % (sql, sort_by.replace('order by','ORDER BY'))
            else:
                order = stringToTuple(sort_by)
                sql = '%s ORDER BY %s' % (sql, ','.join(order))

        elif sort_by is not None:
            errmsg = "Invalid type for 'sort_by' argument : %s"
            raise TypeError, errmsg % type(columns)

        if fetch == 'all':
            results = self.cursor().execute(sql).fetchall()
            if len(results) < 1: return None
            elif result_type is None: return results
            else: return self._restructure(result_type, table_name, results,
                                           self.cursor())

        elif fetch == 'iterator':
            return SqliteRowIterator(self, sql, result_type)

        elif isinstance(fetch, int):
            results = self.cursor().execute(sql).fetchmany(fetch)
            if len(results) < 1: return None
            elif result_type is None: return results
            else: return self._restructure(result_type, table_name, results,
                                           self.cursor())
        else: return sql

    SELECT = _select

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _update(self, table_name, column_data, wherer):
        if where is None:
            raise IndexError, 'Cannot update a record without where clause.'

        if isinstance(column_data, basestring):
            changes = column_data

        elif isinstance(column_data, (tuple,list)):
            to_change = [ ]
            for column in column_data:
                if isinstance(column, basestring):
                    to_change.append(column)
                elif isinstance(column, (tuple,list)):
                    to_change.append('%s=%s' % formatForSql(value))
            changes = ','.join(to_change)

        elif isinstance(column_data, dict):
            to_change = [ ]
            for key, value in column_data.items():
                to_change.append('%s=%s' % (key, formatForSql(value)))
            changes = ', '.join(to_change)

        else:
            errmsg = "Invalid type for 'column_data' argument : %s"
            raise TypeError, errmsg % type(column_data)

        UPR = "UPDATE OR ROLLBACK %s SET %s %s"
        sql = UPR % (table_name, changes, where)
        self.execute(sql)
        self.commit()

    UPDATE = _update


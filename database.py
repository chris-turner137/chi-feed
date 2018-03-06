import os
import sqlite3
from contextlib import closing
from collections import namedtuple

def db_configure(connection):
  """ Ensure that the database is valid. """
  with closing(connection.cursor()) as cursor:
    # Check if version table exists
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='version';")
    table = cursor.fetchone()[0] == 1
    if not table:
      # If it does not exist then the database was uninitialised
      cursor.execute('CREATE TABLE `version` (id STRING UNIQUE, semver STRING);')
      cursor.execute('CREATE TABLE IF NOT EXISTS `entries` (id STRING UNIQUE, dump STRING);')
      cursor.execute('CREATE TABLE IF NOT EXISTS `classify` (entry STRING, edge STRING, touched STRING);')
      cursor.execute('INSERT INTO version VALUES (?,?);', ('schema', '0.0.0'))

    # Get schema version
    cursor.execute("SELECT semver FROM version WHERE id='schema';")
    row = cursor.fetchone()
    schema_semver = row[0] if row is not None else None

    # Update from unversioned to 0.0.0
    if schema_semver == None:
      cursor.execute('INSERT INTO version VALUES (?,?);', ('schema', '0.0.0'))
      schema_semver = '0.0.0'

    # Update from 0.0.0 to 0.0.1
    if schema_semver == '0.0.0':
      from database_upgrade import db_upgrade_0_0_0_to_0_0_1
      schema_semver = db_upgrade_0_0_0_to_0_0_1(connection)

    return schema_semver

  connection.commit()

if __name__ == '__main__':
  print("Schema version (curr):", '0.0.1')

  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  with sqlite3.connect('.chi/feed/entries.db') as connection:
    connection.isolation_level = None

    # Ensure that the database is initialised
    print("Schema version (actu):", db_configure(connection))

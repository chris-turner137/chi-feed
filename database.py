import os
import sqlite3
from contextlib import closing

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
      cursor.execute('INSERT INTO version VALUES (?,?)', ('schema', '0.0.0'))

    # Get schema version
    cursor.execute("SELECT semver FROM version WHERE id='schema';")
    row = cursor.fetchone()
    schema_semver = row[0] if row is not None else None

    # TODO: Check schema is as expected

  connection.commit()

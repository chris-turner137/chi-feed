import os
import sqlite3
from contextlib import closing
from datetime import datetime
from chi_feed import load_flow_config

def db_upgrade_0_0_0_to_0_0_1(connection):
  with closing(connection.cursor()) as cursor:
    cursor.execute('CREATE TABLE `receipts` (entry STRING,\
                                             node STRING,\
                                             outlet STRING,\
                                             touch STRING,\
                                             UNIQUE(entry, node));')

    # Backtrack the flow configuration to find labelling rules
    flow = load_flow_config()
    rules = []
    for e in flow['edges']:
      c = [(e,n['id'],o,n['inlets'])
           for n in flow['nodes'] if len(n['inlets']) == 1
           for o in n['outlets'] if o['edge'] == e]
      if len(c) == 1:
        rules.append(c[0])

    # Fabricate receipts
    cursor.execute('SELECT entry, edge FROM `classify`;')
    now = datetime.now().isoformat()
    for row in cursor:
      entry, edge = row
      while True:
        for e,n,o,i in rules:
          if e == edge:
            connection.execute('INSERT INTO receipts VALUES (?,?,?,?);',
                               (entry, n, o['answer'], now))
            edge = i[0]
            break
        else:
          break

    cursor.execute("UPDATE version SET `semver`='0.0.1' WHERE `id`=='schema';")
  return '0.0.1'

def db_upgrade_0_0_1_to_0_0_2(connection):
  with closing(connection.cursor()) as cursor:
    # Create replacement table
    cursor.execute('CREATE TABLE `tags` (entry STRING,\
                                         tag STRING,\
                                         modified STRING,\
                                         touched STRING);')

    # Copy the data into the new table
    cursor.execute('INSERT INTO tags SELECT entry, edge, touched, touched FROM `classify`;')

    # Remove the old table
    cursor.execute('DROP TABLE `classify`;')

    cursor.execute("UPDATE version SET `semver`='0.0.2' WHERE `id`=='schema';")
  return '0.0.2'

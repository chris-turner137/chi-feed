"""
Fetch and process articles from RSS feeds.

Usage:
  chi-feed init
  chi-feed add [<source>]
  chi-feed list
  chi-feed fetch [<id>]
  chi-feed flow
  chi-feed search [<query>]

Options:
  -h --help  Show this help.
"""
from docopt import docopt
import sys
import os, errno
import json
import feedparser
import sqlite3
from contextlib import closing
from builtins import input
from datetime import datetime
from collections import namedtuple
from query import get_parser, QueryLambdaTransformer

def feed_fromRSS(source, rss):
  """
  Convert a source and feedparser feed description into an internal feed
  configuration.
  """
  return {
    'id': source, # Name to refer to in queries
    'source': source, # Location to fetch from
    'title': rss.title, # Human-friendly title
    'dump': json.dumps(rss) # Save for future reference
  }

def load_feeds_config():
  # If the file doesn't exists the feed list is empty
  try:
    with open('.chi/feed/feeds.json', 'r') as f:
      # TODO: Perhaps this ought to be validated
      return json.load(f)
  except FileNotFoundError as e:
    return []
  except:
    raise NotImplementedError

def save_feeds_config(config):
  try:
    with open('.chi/feed/feeds.json', 'w') as f:
      json.dump(config, f, indent=2)
  except:
    raise NotImplementedError

def command_feed_init(args):
  """ Create the filesystem structure for a valid chi-feed instance. """
  try:
    # Create the .chi/feed directory
    os.makedirs('.chi/feed')
  except OSError as e:
    if e.errno == errno.EEXIST:
      # Already exists
      pass
    else:
      # Something else
      raise
  except:
    raise NotImplementedError

def db_configure(connection):
  """ Ensure that the database is valid. """
  with closing(connection.cursor()) as cursor:
    try:
      cursor.execute('CREATE TABLE IF NOT EXISTS `entries` (id STRING UNIQUE, dump STRING);')
      cursor.execute('CREATE TABLE IF NOT EXISTS `classify` (entry STRING, edge STRING, touched STRING);')
    except:
      raise NotImplementedError

  # TODO: Check that the format of the tables is as expected.
  connection.commit()

Entry = namedtuple('Entry', ['id', 'title', 'dump'])

def entry_fromRow(row):
  id, dump = row
  dump = json.loads(dump)
  return Entry(id=id, title=dump['title'], dump=dump)

def store_new_entries(entries):
  """ Add new entries to the database. """
  flow = load_flow_config()
  with sqlite3.connect('.chi/feed/entries.db') as connection:
    connection.isolation_level = None

    # Ensure that the database is initialised
    db_configure(connection)

    # Add all entries where there is no contrain violation.
    now = datetime.now().isoformat()
    with closing(connection.cursor()) as cursor:
      added = 0
      for entry in entries:
        try:
          cursor.execute('INSERT INTO `entries` VALUES (?,?);',
                         (entry['id'], json.dumps(entry)))
          cursor.execute('INSERT INTO `classify` VALUES (?,?,?);',
                         (entry['id'], flow['source'], now))
          added += 1
        except sqlite3.DatabaseError as e:
          # Ignore attempts to add duplicate entries
          if e.args[0] != 'UNIQUE constraint failed: entries.id':
            raise
          print('Ignored duplicate entry with id "{}"'.format(entry.id))
        except sqlite3.DatabaseError as e:
          print(e)
          raise
      print('Entries added', added)
      connection.commit()

def command_feed_add(args):
  """ Add an RSS feed to track. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # Fetch and parse the RSS feed
  try:
    rss = feedparser.parse(args['<source>'])
    if rss.bozo == 1:
      raise rss.bozo_exception
  except:
    raise NotImplementedError

  # Append the feed to the configuration file
  feed = feed_fromRSS(args['<source>'], rss.feed)
  feeds = load_feeds_config()
  feeds.append(feed)
  save_feeds_config(feeds)

  # Dumps the feed description to stdout
  if sys.stdout.isatty():
    print('Added feed "{}" ({}).'.format(feed['id'], feed['title']))
  else:
    print(json.dumps(feed, indent=2))

  # Add new entries to the database
  store_new_entries(rss['entries'])

def command_feed_list(args):
  """ List tracked RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # Load the feeds configuration
  feeds = load_feeds_config()

  try:
    if sys.stdout.isatty():
      # Human-readable output
      for feed in feeds:
        print('* {} ({})'.format(feed['id'], feed['title']))
    else:
      # Machine-readable output
      for feed in feeds:
        print(json.dumps(feed))
  except:
    raise NotImplementedError
  return 0

def command_feed_fetch(args):
  """ Fetch articles from RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # Load the feeds configuration
  feeds = load_feeds_config()

  matched = False
  for feed in feeds:
    # Check the feed matches the specification
    if args['<id>'] is not None and args['<id>'] != feed['id']:
      continue
    matched = True

    # Fetch the feed
    print('Fetching feed "{}".'.format(feed['id']))

    # Fetch and parse the RSS feed
    try:
      rss = feedparser.parse(feed['source'])
      if rss.bozo == 1:
        raise rss.bozo_exception
    except:
      raise NotImplementedError

    # Add new entries to the database
    store_new_entries(rss['entries'])

  if not matched:
    print("No feeds to fetch.")
    return 1
  return 0

def load_flow_config():
  # If the file doesn't exists then use the default flow
  try:
    with open('.chi/feed/flow.json', 'r') as f:
      # TODO: Perhaps this ought to be validated
      return json.load(f)
  except FileNotFoundError as e:
    default = {
      'edges': ['unread', 'starred', 'unstarred'],
      'source': 'unread',
      'nodes': [
        {
          'id': 'check-unread',
          'description': 'Should I star this for later?',
          'inlets': ['unread'],
          'outlets': [{'answer': 'y', 'edge': 'starred'},
                      {'answer': 'n', 'edge': 'unstarred'}]
        },
        {
          'id': 'check-starred',
          'description': 'Should I remove this star?',
          'inlets': ['starred'],
          'outlets': [{'answer': 'y', 'edge': 'unstarred'},
                      {'answer': 'n', 'edge': 'starred'}]
        }
      ]
    }
    with open('.chi/feed/flow.json', 'w') as f:
      json.dump(default, f, indent=2)
    return default
  except:
    raise NotImplementedError

def command_feed_flow(args):
  """ Process articles from RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # Load the flow configuration
  flow = load_flow_config()

  for node in flow['nodes']:
    while True:
      with sqlite3.connect('.chi/feed/entries.db') as connection:
        connection.isolation_level = None

        # Ensure that the database is initialised
        db_configure(connection)

        with closing(connection.cursor()) as cursor:
          # Get the first entry matching one of the inlets
          cursor.execute('SELECT ROWID, * FROM `classify` WHERE `edge` IN (?) ORDER BY `touched` LIMIT 1;',
                         node['inlets'])
          row = cursor.fetchone()
          if row is None:
            break
          rowid, entry, edge, _ = row

          # Lookup the entry in the entry table
          cursor.execute('SELECT * FROM `entries` WHERE `id` == ?;', (entry,))
          row = cursor.fetchone()
          assert cursor.fetchone() is None

          # Display the entry and question
          entry = entry_fromRow(row)
          print('Q: {} ({})'.format(node['id'], node['description']))
          print('\n{}: {}\n'.format(edge, entry))
          print('#', entry.title)
          print()
          print(json.loads(row[1])['summary'])
          print()

          # Prompt for input
          print('q = Quit, ', end='')
          print(', '.join('{} = {}'.format(outlet['answer'], outlet['edge'])
                for outlet in node['outlets']))
          print('? ', end='')
          s = input()

          # If 'q' is entered then quit the session
          if s == 'q':
            return 0

          # If no input was provided touch the row and move on
          elif s == '':
            cursor.execute('UPDATE `classify` SET `touched` = ? WHERE ROWID == ?;',
                           (datetime.now().isoformat(), rowid))
            print('Touched row(s)', cursor.rowcount)
            connection.commit()
            continue

          # Otherwise find the associated outlet and reclassify the entry accordingly
          else:
            for outlet in node['outlets']:
              if s == outlet['answer']:
                # 
                cursor.execute('UPDATE `classify` SET `edge` = ?, `touched` = ? WHERE ROWID == ?;',
                               (outlet['edge'], datetime.now().isoformat(), rowid))
                print('Reclassified row(s)', cursor.rowcount)
                connection.commit()
                break
            else:
              raise NotImplementedError
  return 0

def db_query():
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError
  with sqlite3.connect('.chi/feed/entries.db') as connection:
    connection.isolation_level = None

    # Ensure that the database is initialised
    db_configure(connection)

    # Perform the search
    with closing(connection.cursor()) as cursor:
      connection.commit()
      try:
        cursor.execute('SELECT * FROM `entries`;')
        i = 0
        for row in cursor:
          yield entry_fromRow(row)
      except Exception as e:
        raise NotImplementedError
  return

def pipe_query():
  for line in sys.stdin:
    d = json.loads(line)
    yield Entry(d['id'], d['title'], d['dump'])

def command_feed_search(args):
  """ Search database of articles built from RSS feeds. """
  if args['<query>'] is not None:
    # Parse the query
    tree = get_parser().parse(args['<query>'])
    print(tree.pretty())

    # Transform it into a predicate
    predicate = QueryLambdaTransformer().transform(tree)
  else:
    # Default to returning everything
    predicate = lambda x: True

  # If input is from a terminal then use the local database as source otherwise
  # take stdin as the datasource.
  if sys.stdin.isatty():
    source = db_query()
  else:
    source = pipe_query()

  try:
    with closing(source) as results:
      for x in filter(predicate, results):
        if sys.stdout.isatty():
          print('{} ({})'.format(x.id, x.title))
        else:
          print(json.dumps(x._asdict()))
  except Exception as e:
    raise NotImplementedError

def command_feed(args):
  if args['init']:
    return command_feed_init(args)  
  elif args['add']:
    return command_feed_add(args)
  elif args['list']:
    return command_feed_list(args)
  elif args['fetch']:
    return command_feed_fetch(args)
  elif args['flow']:
    return command_feed_flow(args)
  elif args['search']:
    return command_feed_search(args)
  else:
    raise NotImplementedError

if __name__ == '__main__':
  # Parse command line arguments
  args = docopt(__doc__, version='chi-feed 1.0')

  retval = command_feed(args)
  sys.exit(retval)

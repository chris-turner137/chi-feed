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
import warnings
from contextlib import closing
from builtins import input
from datetime import datetime
from collections import namedtuple
from query import get_parser, QueryLambdaTransformer
from database import db_configure
from html.parser import HTMLParser

class MLStripper(HTMLParser):
  def __init__(self):
    self.reset()
    self.strict = False
    self.convert_charrefs= True
    self.fed = []

  def handle_data(self, d):
    self.fed.append(d)

  def get_data(self):
    return ''.join(self.fed)

def strip_tags(html):
  s = MLStripper()
  s.feed(html)
  return s.get_data()

class Terminal(object):
  BOLD = '\033[1m'
  NORM = '\033[0m'
  def __init__(self):
    pass

  def __call__(self, *args):
    return self.fromMarkdown(' '.join(map(str, args)))

  def fromMarkdown(self, source):
    def fmt_line(line):
      idx_hash = line.find('#')
      if idx_hash != -1:
        return line[:idx_hash] + Terminal.BOLD + line[idx_hash:] + Terminal.NORM
      return line
    return '\n'.join(map(fmt_line, source.splitlines()))

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

Entry = namedtuple('Entry', ['id', 'title', 'authors', 'dump'])

def entry_fromRow(row):
  id, dump = row
  dump = json.loads(dump)
  return Entry(id=id, authors=dump['author'], title=dump['title'], dump=dump)

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
          cursor.execute('INSERT INTO `tags` VALUES (?,?,?,?);',
                         (entry['id'], flow['source'], now,''))
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
    except feedparser.CharacterEncodingOverride as e:
      warnings.warn('Ignoring feed exception "{}"'.format(repr(e)))
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
          cursor.execute('SELECT ROWID, entry, tag FROM `tags`\
                          WHERE `tag` IN (?)\
                          ORDER BY `touched` ASC, `modified` DESC LIMIT 1;',
                         node['inlets'])
          row = cursor.fetchone()
          if row is None:
            break
          rowid, entry, tag = row

          # Lookup the entry in the entry table
          cursor.execute('SELECT * FROM `entries` WHERE `id` == ?;', (entry,))
          row = cursor.fetchone()
          assert cursor.fetchone() is None

          # Display the entry and question
          entry = entry_fromRow(row)
          print('Q: {} ({})'.format(node['id'], node['description']))
          print('\n{}\n'.format(tag))
          print(Terminal()('#', entry.title))
          print()
          print(strip_tags(entry.authors))
          print()
          print(strip_tags(json.loads(row[1])['summary']))
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
            cursor.execute('UPDATE `tags` SET `touched` = ? WHERE ROWID == ?;',
                           (datetime.now().isoformat(), rowid))
            print('Touched row(s)', cursor.rowcount)
            connection.commit()
            continue

          # Otherwise find the associated outlet and retag the entry accordingly
          else:
            for outlet in node['outlets']:
              if s == outlet['answer']:
                now = datetime.now().isoformat()
                cursor.execute('UPDATE `tags` SET `tag`=?, `touched`=?, `modified`=? WHERE ROWID == ?;',
                               (outlet['edge'], now, now, rowid))
                cursor.execute('INSERT INTO receipts VALUES (?,?,?,?);',
                               (entry.id, node['id'], outlet['answer'], now))
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

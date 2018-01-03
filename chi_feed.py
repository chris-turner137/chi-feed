"""
Fetch and process articles from RSS feeds.

Usage:
  chi-feed init
  chi-feed add [<source>]
  chi-feed list
  chi-feed fetch
  chi-feed flow
  chi-feed search

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

def feed_fromRSS(source, rss):
  """
  Convert a source and feedparser feed description into an internal feed
  configuration.
  """
  return {
    'id': source, # Name to refer to in and queries
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
      json.dump(config, f)
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

  raise NotImplementedError

def db_configure(connection):
  """ Ensure that the database is valid. """
  with closing(connection.cursor()) as cursor:
    try:
      cursor.execute('CREATE TABLE IF NOT EXISTS `entries` (id STRING UNIQUE, dump STRING);')
    except:
      raise NotImplementedError

  # TODO: Check that the format of the tables is as expected.
  connection.commit()

def command_feed_add(args):
  """ Add an RSS feed to track. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # Fetch and parse the RSS feed
  try:
    rss = feedparser.parse(args['<source>'])
  except:
    raise NotImplementedError

  # Append the feed to the configuration file
  feed = feed_fromRSS(args['<source>'], rss.feed)
  feeds = load_feeds_config()
  feeds.append(feed)
  save_feeds_config(feeds)

  # Dumps the feed description to stdout
  print(json.dumps(rss.feed, indent=2))
  print(json.dumps(feed, indent=2))

  # Add new entries to the database
  with sqlite3.connect('.chi/feed/entries.db') as connection:
    # Ensure that the database is initialised
    db_configure(connection)

    # Add all entries where there is no contrain violation.
    with closing(connection.cursor()) as cursor:
      added = 0
      for entry in rss['entries']:
        try:
          cursor.execute('INSERT INTO `entries` VALUES (?,?);',
                         (entry['id'], json.dumps(entry)))
          added += 0
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

def command_feed_list(args):
  """ List tracked RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # Load the feeds configuration
  feeds = load_feeds_config()
  print(json.dumps(feeds, indent=2))
  return 0

def command_feed_fetch(args):
  """ Fetch articles from RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError
  raise NotImplementedError

def command_feed_flow(args):
  """ Process articles from RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError
  raise NotImplementedError

def command_feed_search(args):
  """ Search database of articles built from RSS feeds. """
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  with sqlite3.connect('.chi/feed/entries.db') as connection:
    # Ensure that the database is initialised
    db_configure(connection)

    # Perform the search
    print('Entries:')
    with closing(connection.cursor()) as cursor:
      connection.commit()
      try:
        cursor.execute('SELECT * FROM `entries`;')
        i = 0
        for i, row in enumerate(cursor):
          print(row)
        print("Row(s) affected: ", i)
      except Exception as e:
        raise NotImplementedError

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

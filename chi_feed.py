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
import os, errno
import json

def load_feeds_config():
  if not os.path.exists('.chi/feed'):
    raise NotImplementedError

  # If the file doesn't exists the feed list is empty
  try:
    with open('.chi/feed/feeds.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError as e:
    return []
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

def command_feed_add(args):
  """ Add an RSS feed to track. """
  raise NotImplementedError

def command_feed_list(args):
  """ List tracked RSS feeds. """
  feeds = load_feeds_config()
  print(feeds)

def command_feed_fetch(args):
  """ Fetch articles from RSS feeds. """
  raise NotImplementedError

def command_feed_flow(args):
  """ Process articles from RSS feeds. """
  raise NotImplementedError

def command_feed_search(args):
  """ Search database of articles built from RSS feeds. """
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

  command_feed(args)

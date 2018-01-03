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

def command_feed_init(args):
  """ Create the filesystem structure for a valid chi-feed instance. """
  raise NotImplementedError

def command_feed_add(args):
  """ Add an RSS feed to track. """
  raise NotImplementedError

def command_feed_list(args):
  """ List tracked RSS feeds. """
  raise NotImplementedError

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

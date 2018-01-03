# chi-feed

Fetch and process articles from RSS feeds.

Usage:
* chi-feed init
* chi-feed add [<source>]
* chi-feed list
* chi-feed fetch [<id>]
* chi-feed flow
* chi-feed search

Status: just about functional, wholly unstable.

## Subcommands

### `chi-feed init`

Create the internal directory structure, marking the directory as a valid location to issue the other chi-feed commands.

### `chi-feed add <source>`

Add a feed.

### `chi-feed list`

List feeds.

### `chi-fetch`

Fetch new results from feeds.

### `chi-feed flow`

Prompt article summarys and poses a classification question as defined in the flow.
The user answers the question for the article to be reclassified or ignore it to postpose.

### `chi-feed search`

Lists all the entries in the database.
In the future this should allow the results to be filtered in accordance with a query.
In the meantime you might `grep` the results.

## Configuration

For manipulating the configuration in ways not exposed in the command-line interface the `.chi/feed/feeds.json` and `.chi/feed/flow.json` files may be modified with a text editor.
This is *of-course* undocumented and potentially unstable.

## Filesystem structure

* .chi/feed/feeds.json
* .chi/feed/flow.json
* .chi/feed/entries.db

# chi-feed

## Filesystem structure

* .chi/feed/feeds.json
* .chi/feed/flow.json
* .chi/feed/<entry db>

SQLite entry database
* Table `entries`
* Table `classifications`

## Workflow

### `chi-feed init`

Create directory structure.

### `chi-feed add`

Add feeds.

### `chi-feed list`

List feeds.

### `chi-fetch`

Fetch new results from feeds.

### `chi-feed flow`

Prompt with questions?
Can classify, postpone, pass to chi-action

### `chi-feed search`

Query on simple things only chi-feed knows about.

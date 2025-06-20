# Metamoney

## Commands

Commands are based on the _output_ rather than a _verb_ i.e. this is a
declarative system.

```sh
# Import from an exported Cathay Bank transactions file and export as
# a list of transactions in a given format.
metamoney transactions --source 20250617-cathay.csv --institution cathay_tw --output 20250617-cathay.beancount
# Scrape Cathay Bank for transaction records, ingest them, and export
# as a list of transactions in a given format.
metamoney transactions --source remote --institution cathay_tw --output 20250617-cathay.beancount
# The same, but from stdin; equivalent to --source stdin
metamoney transactions --institution cathay_tw --output 20250617-cathay.beancount

# Implicit flags
--source / -s
--output / -o
--institution cathay_tw # this could be a normal part of the command, but keeping it as a mandatory flag imho makes the interface easier to understand
--input-format csv
--output-format beancount
```

## Configuration

Metamoney has 3 configuration files:

- `accounts.yml`
- `map.yml`
- `config.yml`

By default, they are stored in the `$HOME/.metamoney` folder. **Only config.yml
is safe to commit to version control.** `accounts.yml` contains information
about accounts and may contain credentials. `map.yml` contains information about
institutions and may tell people something about your spending habits.

## Versioning

Metamoney uses a short SemVer scheme: `VERSION.BUILD`. Build is iterated
automatically for every commit on main, while `VERSION` is manually updated.

When `VERSION` is updated, `BUILD` will be reset to `1`. Before reaching MVP,
`VERSION` will be set to `0`. `VERSION` is expected to be incremented when a new
user-facing feature is released.

No distinction is drawn between major, minor, and patch releases, because the
intention is to enable rapid iteration by automating publication and testing.

No particular promises are made about the stability or compatibility of any
version.

# Metamoney

Metamoney aims to combine numerous personal finance tools into a 'swiss army
knife' of finance functions, while remaining extensible, scriptable, and
agnostic about I/O formats.

v1.0 should replace a number of older tools I've written:

- [minibudget](https://github.com/fdavies93/minibudget) - write simple budgets
  and automatically generate reports
- [seneca](https://github.com/fdavies93/seneca) - convert Wise multi-currency
  statements to Beancount format
- [redbeancount](https://github.com/fdavies93/redbeancount) - convert several
  Asian banks' statements to Beancount format

Therefore the tool must:

- Be able to produce projections such as budgets.
- Handle multi-currency transactions coherently.
- Allow for I/O in different formats.
- Let users extend the system with their own I/O formats and institutions.

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

Metamoney is configured by dynamically importing `$HOME/.metamoney/__init__.py`
as a Python module (if it exists).

In `config.py` you can set up your variables however you like. This means, for
example, that you can load credentials from a local plain-text file, from an ENV
variable, or even from a secrets manager or keychain.

Since `config.py` will usually contain sensitive information, we recommend NOT
committing it to version control unless you know what you're doing and have
taken steps to hide secrets like financial account details. Instead, consider
using an encrypted backup solution such as [restic](https://restic.net/) or
[borg](https://www.borgbackup.org).

For more information on the config variables exported to metamoney, see
[config documentation](./docs/configuration.md).

## Technical Information

### Versioning

Metamoney uses a short CalVer scheme: `YEAR.SERIAL`

When `YEAR` is updated, `SERIAL` will be reset to `0`. Before reaching MVP,
`YEAR` will be set to `0`. `SERIAL` is expected to be incremented when a new
user-facing feature is released. No distinction is drawn between major, minor,
and patch releases.

No particular promises are made about the stability or compatibility of any
version, except that we hope that stability improves over time. If you want to
guarantee stable behaviour, consider using a fixed version in your package
manager. On the other hand, if you want rolling releases, consider installing
this package directly from the git repository.

### License

Metamoney is released under
[AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html).

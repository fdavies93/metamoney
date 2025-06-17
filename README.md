# Metamoney

## Commands

Commands should be based on the _output_ rather than a _verb_ i.e. this is a
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

# Configuring MetaMoney

## Getting Started

...

### Editor Setup

While references to the metamoney package will work at runtime, your editor may
not immediately pick them up. This is because of the limitations of dynamic
module loading in Python.

To fix this, make sure that your editor is running in an environment which has
access to the metamoney package. If you are running metamoney from source just
enter the virtual environment. If you have installed metamoney independently,
e.g. with `pipx`, consider starting a `pyproject.toml` in `$HOME/metamoney` and
installing `metamoney` from this package.

For GUI editors like VSCode, you can then set your Python runtime to be the
runtime for the venv. For CLI-based editors like Neovim, activate the venv and
start the editor.

## Configuration Variables

### `mappings`

`mappings` is a collection of `mapping` objects. Each mapping has a single
condition (which can be joined using `AllCondition` or `AnyCondition`) to be
applied, and a number of remapping functions to apply to a journal entry.

For example:

```py
mappings = [
    Mapping(
        AllCondition(
            TransactionFieldMatchesCondition("account", "^Assets.*"),
            TransactionFieldMatchesCondition("payee", "VULTR.*"),
        ),
        (
            AddCounterTransactionRemap("Expenses:True-Expenses:Subscriptions"),
            SetNarrationRemap("Vultr"),
        ),
    )
]
```

Here we check that some transaction in the journal is of type `Assets`, which
usually means that it comes directly from a financial statement. We also check
that the payee of this transaction matches the regular expression `VULTR.*`. We
then apply `AddCounterTransactionRemap` to create the balancing transaction to
an `Expenses` account, and `SetNarrationRemap` to change the narration of the
journal entry.

Note that you can easily write your own remapping and condition functions and
shortcuts provided they adhere to the same interface as the built-in ones.

See [mapper.py](../src/metamoney/mappers/mapper.py) for all remapping and
condition shortcuts.

### `importers`

This exports custom importers which can be subclassed from `AbstractImporter`.
You need to set up the functions `data_source()` and `data_institution()` to
return information about the institution so that metamoney can find the
appropriate importer.

Custom importers take precedence over built-in importers if they refer to the
same institution and file type.

For a more complete reference take a look at
[importers](../src/metamoney/importers).

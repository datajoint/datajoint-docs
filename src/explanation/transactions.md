# Transactions

A database is not merely a store of records; it is meant to reflect the current
state of an enterprise faithfully, to everyone looking at it at once. Two
analysts querying the same pipeline should see the same data, and a write made by
one should immediately inform every read that follows. This property is called
**data consistency**, and it is easiest to appreciate through its failures — a
bank website that shows yesterday's pending transactions but today's balance is
briefly inconsistent, presenting two versions of the truth that do not agree.

Consistency is cheap when only one party writes and everyone else reads, which is
common in science: one lab produces data, others analyze it. It becomes hard the
moment several agents — people or processes — read and modify the same data
concurrently. The mechanism that keeps a database consistent under concurrent,
multi-step change is the **transaction**: a group of statements that the database
treats as a single indivisible unit.

## What a transaction guarantees

A transaction bundles several read and write operations so that they commit
**all-or-nothing**. Either every operation in the group takes effect together, or
— if anything goes wrong — none of them do, and the database is left exactly as
it was before the group began. There is no observable state in which only some of
the operations have landed.

Relational databases express this guarantee through the **ACID** properties.
Grounded in DataJoint, they read as follows:

- **Atomic** — the group is indivisible. If any step fails or raises, the whole
  group is rolled back. This is the all-or-nothing behavior above.
- **Consistent** — each committed transaction moves the database from one valid
  state to another, with every integrity constraint — primary keys, foreign
  keys, `unique` — satisfied at the boundary. A transaction that would leave a
  dangling foreign key cannot commit.
- **Isolated** — concurrent transactions do not see one another's partial work.
  Each runs as if it had the database to itself, reading a consistent snapshot.
- **Durable** — once a transaction commits, its changes survive crashes and
  restarts.

DataJoint adheres to this classical ACID model on both of its peer backends,
MySQL and PostgreSQL, using serializable-style isolation for operations that must
be atomic. The database engine, not DataJoint, ultimately enforces the guarantee;
DataJoint's job is to open a transaction around the right group of statements.

## A concrete all-or-nothing example

The textbook case is a transfer between two accounts. Consider a simple table of
bank accounts:

```python
import datajoint as dj

schema = dj.Schema("bank")

@schema
class Account(dj.Manual):
    definition = """
    account_number : int32
    ---
    customer_name  : varchar(60)
    balance        : decimal(9, 2)
    """
```

Moving money requires two writes that belong together: debit the source, credit
the destination. Written naively, without grouping them, a failure between the
two is catastrophic:

```python
def transfer_unsafe(source, destination, amount):
    balance = (Account & source).fetch1("balance")
    if balance < amount:
        raise RuntimeError("Insufficient funds")
    Account.update1(dict(source, balance=balance - amount))   # money leaves here
    raise RuntimeError("connection lost")                     # ...and never arrives
    Account.update1(dict(destination, balance=... + amount))  # never runs
```

The debit committed on its own; the credit never happened. Money vanished, and no
constraint was violated — the database is internally valid but factually wrong.
Wrapping the two writes in a transaction closes this gap:

```python
def transfer(source, destination, amount):
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")
    with dj.conn().transaction:
        balance = (Account & source).fetch1("balance")
        if balance < amount:
            raise RuntimeError("Insufficient funds")
        Account.update1(dict(source, balance=balance - amount))
        dest = (Account & destination).fetch1("balance")
        Account.update1(dict(destination, balance=dest + amount))
```

Everything inside `with dj.conn().transaction:` is one atomic unit. If the block
completes normally, both updates commit together. If any statement raises — an
insufficient-funds check, a lost connection, a bug — the whole block rolls back
and the exception propagates. The debit is never left stranded without its credit.

The same pattern makes a **master row and its part rows** land together. Because
a part table's rows depend on their master through a foreign key, inserting them
as one transaction guarantees you never observe a master without its parts, nor
parts orphaned from a master:

```python
with dj.conn().transaction:
    Experiment.insert1(dict(experiment_id=1, experiment_date="2026-07-17"))
    Experiment.Trial.insert([
        dict(experiment_id=1, trial_idx=1, outcome="success"),
        dict(experiment_id=1, trial_idx=2, outcome="failure"),
    ])
```

A single `insert()` or `update1()` call is *already* atomic on its own. You reach
for an explicit `with dj.conn().transaction:` block only when **several**
operations must succeed or fail as a group, as above.

!!! warning "Transactions do not nest"
    DataJoint does not support nested transactions. Opening a transaction while
    another is already active on the same connection raises an error. Keep exactly
    one `transaction` block active at a time.

## Transactions in computation

You almost never write a transaction block inside a `make()` method, because
`populate()` has already opened one for you. For each key it processes,
`populate()` wraps the entire `make(key)` call in a transaction, calls `make()`,
and commits only if it returns without error. Everything a `make()` writes — its
own rows and all of its part-table rows — is therefore inserted as one atomic
unit. A computed result and its parts commit together, or, if `make()` raises,
roll back together, leaving nothing behind to clean up.

```python
@schema
class ProcessedData(dj.Computed):
    definition = """
    -> RawData
    ---
    result : float64
    """

    def make(self, key):
        data = (RawData & key).fetch1("data")
        result = expensive_computation(data)
        self.insert1(dict(key, result=result))   # already inside populate()'s transaction
```

This is why DataJoint pipelines stay consistent with their inputs: a downstream
result is either fully present or fully absent, never half-computed.

!!! danger "Never open a transaction inside `make()`"
    Because `populate()` has already started one, opening your own transaction
    inside `make()` attempts to nest — which DataJoint does not support, so it
    raises an error. Just insert directly; the write is already atomic.

    ```python
    def make(self, key):
        with dj.conn().transaction:   # WRONG — a transaction is already active
            self.insert1(...)         # this raises an error
    ```

For long-running computations, holding the transaction open for the whole `make()`
would lock resources and risk timeouts. The [three-part make](computation-model.md)
pattern addresses this by running fetch and compute *outside* the transaction and
confining only the insert to a brief one — still without you ever opening a
transaction yourself.

## Deletes are transactional too

Cascading deletes span many tables — a delete propagates through every dependent
table in reverse topological order. To keep that cascade all-or-nothing, `delete`
runs inside a transaction by default (`transaction=True`), so a failure partway
through rolls back the entire cascade rather than leaving descendants deleted and
ancestors intact. The only reason to opt out with `delete(transaction=False)` is
when the delete is already running inside a transaction you opened, since a nested
transaction is not allowed.

## See also

- [Computation Model](computation-model.md) — how `populate()` wraps each
  `make()` call and the three-part pattern for long computations.
- [Data Integrity](data-integrity.md) — the integrity guarantees transactions
  uphold at each commit boundary.
- [Insert data](../how-to/insert-data.md) — inserting master and part rows.
- [Delete data](../how-to/delete-data.md) — cascading deletes and safemode.
- [AutoPopulate](../reference/specs/autopopulate.md) — normative spec for the
  per-key transaction and the make() reproducibility contract.

# Traversal Shape Catalog

Worked examples of `Diagram.expand`, one per schema shape that the [Traversal specification](diagram.md#traversal-specification) distinguishes.

!!! version-added "New in 2.4"
    `Diagram.expand` and the behavior shown here are new in DataJoint 2.4.

## How to read this catalog

Each shape has a tiny schema, a few rows, one or more seeds, and the exact rows `expand` returns. The rows follow from the definitions of `D` and `U` in [Operations](diagram.md#operations); a sentence after each shape says why. The test suite mirrors these shapes one to one, under the same IDs.

- **Directions.** *down* is `dj.Diagram.expand(seed, "down")`, which equals `Diagram.cascade(seed, part_integrity="cascade")`. *up* is `expand(seed, "up")`, which equals `Diagram.trace(seed)`. *both* is `expand(seed, "both")`.
- **Schemas.** Each shape is its own schema, declared with `schema = dj.Schema(...)`; table names repeat across shapes. Tables are `dj.Manual` unless the shape says otherwise.
- **Rows** are written as primary-key tuples, in the order of the primary key. When a column outside the primary key matters, it follows a semicolon: `(1, 2; NULL)` is a row with primary key `(1, 2)` whose foreign-key column is NULL.
- **Results** list every table in the diagram's node set (the [table-level reach](diagram.md#expanded-diagrams)). *none* means the table is a node with zero rows.

| ID | Shape | What it pins down |
|---|---|---|
| [S1](#s1-identity-foreign-key-in-the-primary-key) | Identity foreign key in the primary key | The base case: the condition is copied |
| [S2](#s2-secondary-foreign-key) | Secondary foreign key | Upward crossing is a restriction |
| [S3](#s3-nullable-foreign-key-sharing-a-primary-key-column) | Nullable foreign key sharing a primary-key column | A foreign key with a NULL column references nothing |
| [S4](#s4-renamed-foreign-key) | Renamed foreign key | Crossing through `attr_map`, not by name |
| [S5](#s5-parallel-foreign-keys) | Parallel foreign keys | Separate edges combine with OR |
| [S6](#s6-diamond-with-a-shared-key) | Diamond with a shared key | Paths combine by union |
| [S7](#s7-diamond-reached-through-a-secondary-foreign-key) | Diamond reached through a secondary foreign key | A row reached only through its secondary reference |
| [G1](#g1-part-to-master-lift) | Part-to-master lift | The lift is existential |
| [G2](#g2-part-of-part-with-two-chains) | Part-of-part with two chains | The lift is one step on the master key |
| [G3](#g3-a-second-renamed-foreign-key-to-its-own-master) | A second, renamed foreign key to its own master | Only the owning reference lifts |
| [G4](#g4-renamed-sibling-foreign-key-chained-across-three-instances) | Renamed sibling foreign key, chained across three instances | The group step iterates |
| [G5](#g5-merge-table) | Merge table | A trace reaches the parts of an ancestor master |
| [G6](#g6-a-part-violating-a1) | A part violating A1 | Traversed as a plain table |
| [K1](#k1-seed-restricted-by-a-descendant) | Seed restricted by a descendant | Seeds are materialized before deleting |
| [K2](#k2-self-referencing-seed) | Self-referencing seed | Same, for a seed that reads its own table |
| [K3](#k3-seed-kinds-give-the-same-rows) | Seed kinds give the same rows | Dict, list, string, subquery, `AndList`, `Not` |
| [K4](#k4-djtop-seed) | `dj.Top` seed | `Top` is replaced by its keys |
| [K5](#k5-empty-seeds) | Empty seeds | Nothing in, nothing out |
| [K6](#k6-unrestricted-seed) | Unrestricted seed | All rows, and a warning for a dict that names no attribute |
| [X1](#x1-unloaded-downstream-schema) | Unloaded downstream schema | Schemas are discovered through foreign keys |
| [X2](#x2-group-cycle-refused-at-declaration) | Group cycle refused at declaration | The group quotient stays acyclic |

---

## Foreign-key shapes

### S1. Identity foreign key in the primary key

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_id : int32
    """
```

| Table | Columns | Rows |
|---|---|---|
| `Subject` | `subject_id` | 1, 2 |
| `Session` | `subject_id, session_id` | (1, 1), (1, 2), (2, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Subject & {"subject_id": 1}` | down | `Subject`: 1<br>`Session`: (1, 1), (1, 2) |
| `Session & {"session_id": 1}` | up | `Session`: (1, 1), (2, 1)<br>`Subject`: 1, 2 |

**Why.** The foreign key embeds the parent's whole key under the same names, in the child's primary key, so the condition `subject_id = 1` is copied to `Session` unchanged. Upward, `Subject` is restricted by the restricted sessions, which reference subjects 1 and 2.

### S2. Secondary foreign key

```python
@schema
class Rig(dj.Lookup):
    definition = """
    rig_id : int32
    """


@schema
class Session(dj.Manual):
    definition = """
    session_id : int32
    ---
    -> Rig
    """
```

| Table | Columns | Rows |
|---|---|---|
| `Rig` | `rig_id` | 1, 2, 3 |
| `Session` | `session_id; rig_id` | (1; 1), (2; 1), (3; 2) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Rig & {"rig_id": 1}` | down | `Rig`: 1<br>`Session`: 1, 2 |
| `Session & {"session_id": 3}` | up | `Session`: 3<br>`Rig`: 2 |

**Why.** Downward, the condition names only `rig_id`, the foreign key's own non-null attribute, so it is copied. Upward, the seed's condition names `session_id`, which the foreign key does not carry: `Rig` is restricted by the restricted session's `rig_id`, giving rig 2. Relabeling the dict would drop `session_id` and select every rig.

### S3. Nullable foreign key sharing a primary-key column

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    """


@schema
class Surgery(dj.Manual):
    definition = """
    -> Subject
    surgery_id : int32
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_id : int32
    ---
    -> [nullable] Surgery
    """
```

`Session`'s foreign key to `Surgery` is `(subject_id, surgery_id)`. It shares `subject_id` with `Session`'s primary key, so only `surgery_id` can be NULL.

| Table | Columns | Rows |
|---|---|---|
| `Subject` | `subject_id` | 1, 2 |
| `Surgery` | `subject_id, surgery_id` | (1, 1), (1, 2), (2, 1) |
| `Session` | `subject_id, session_id; surgery_id` | (1, 1; 1), (1, 2; NULL), (1, 3; 2), (2, 1; 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Surgery & {"subject_id": 1}` | down | `Surgery`: (1, 1), (1, 2)<br>`Session`: (1, 1), (1, 3) |
| `Session & {"subject_id": 1, "session_id": 2}` | up | `Session`: (1, 2)<br>`Subject`: 1<br>`Surgery`: none |

**Why.** Session (1, 2) has `subject_id` set and `surgery_id` NULL, so it references no surgery (A2). Downward, the foreign key has a nullable column, so `subject_id = 1` is not copied; a copy would also delete session (1, 2) ([#1590](https://github.com/datajoint/datajoint-python/issues/1590)). Upward, session (1, 2) reaches its subject but no surgery.

### S4. Renamed foreign key

```python
@schema
class Neuron(dj.Manual):
    definition = """
    neuron_id : int32
    """


@schema
class Input(dj.Manual):
    definition = """
    -> Neuron.proj(source_id="neuron_id")
    input_id : int32
    ---
    neuron_id : int32   # a local label, not a foreign key
    """
```

`Input` holds the referenced neuron as `source_id`, and also has an unrelated attribute that happens to be named `neuron_id`.

| Table | Columns | Rows |
|---|---|---|
| `Neuron` | `neuron_id` | 1, 2, 3 |
| `Input` | `source_id, input_id; neuron_id` | (1, 1; 2), (1, 2; 3), (2, 1; 1), (3, 1; 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Neuron & {"neuron_id": 1}` | down | `Neuron`: 1<br>`Input`: (1, 1), (1, 2) |
| `Input & {"source_id": 2, "input_id": 1}` | up | `Input`: (2, 1)<br>`Neuron`: 2 |

**Why.** A renamed foreign key is crossed through its `attr_map` (`source_id` ↔ `neuron_id`), never by attribute name. Copying `neuron_id = 1` to `Input` would match the unrelated label and select inputs (2, 1) and (3, 1).

### S5. Parallel foreign keys

```python
@schema
class Neuron(dj.Manual):
    definition = """
    neuron_id : int32
    """


@schema
class Synapse(dj.Manual):
    definition = """
    -> Neuron
    -> Neuron.proj(target_id="neuron_id")
    """
```

| Table | Columns | Rows |
|---|---|---|
| `Neuron` | `neuron_id` | 1, 2, 3 |
| `Synapse` | `neuron_id, target_id` | (1, 2), (2, 3), (3, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Neuron & {"neuron_id": 1}` | down | `Neuron`: 1<br>`Synapse`: (1, 2), (3, 1) |
| `Synapse & {"neuron_id": 1, "target_id": 2}` | up | `Synapse`: (1, 2)<br>`Neuron`: 1, 2 |
| `Neuron & {"neuron_id": 1}` | both | `Neuron`: 1, 2, 3<br>`Synapse`: (1, 2), (3, 1) |

**Why.** The two foreign keys are separate edges, and a synapse is reached if either one references neuron 1; combining them with AND would select only synapses from neuron 1 to itself, of which there are none. *both* adds neurons 2 and 3, the other ends of the exported synapses; `D(S) ∪ U(S)` would leave them out.

### S6. Diamond with a shared key

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_id : int32
    """


@schema
class Implant(dj.Manual):
    definition = """
    -> Subject
    implant_id : int32
    """


@schema
class Recording(dj.Manual):
    definition = """
    -> Session
    -> Implant
    """
```

`Recording` inherits `subject_id` through both parents, as one shared column.

| Table | Columns | Rows |
|---|---|---|
| `Subject` | `subject_id` | 1, 2 |
| `Session` | `subject_id, session_id` | (1, 1), (1, 2), (2, 1) |
| `Implant` | `subject_id, implant_id` | (1, 1), (1, 2), (2, 1) |
| `Recording` | `subject_id, session_id, implant_id` | (1, 1, 1), (1, 2, 2), (2, 1, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Subject & {"subject_id": 1}` | down | `Subject`: 1<br>`Session`: (1, 1), (1, 2)<br>`Implant`: (1, 1), (1, 2)<br>`Recording`: (1, 1, 1), (1, 2, 2) |
| `Implant & {"subject_id": 1, "implant_id": 1}` | down | `Implant`: (1, 1)<br>`Recording`: (1, 1, 1) |
| `Implant & {"subject_id": 1, "implant_id": 1}` | both | `Implant`: (1, 1)<br>`Recording`: (1, 1, 1)<br>`Subject`: 1<br>`Session`: (1, 1) |
| `Recording & {"subject_id": 1, "session_id": 2, "implant_id": 2}` | up | `Recording`: (1, 2, 2)<br>`Session`: (1, 2)<br>`Implant`: (1, 2)<br>`Subject`: 1 |

**Why.** From `Subject`, both paths carry the same `subject_id`, and their union is the result; nothing is intersected. *both* from the implant adds session (1, 1), the other parent of the exported recording, and the subject.

### S7. Diamond reached through a secondary foreign key

```python
@schema
class Lab(dj.Manual):
    definition = """
    lab_id : int32
    """


@schema
class Rig(dj.Manual):
    definition = """
    rig_id : int32
    ---
    -> Lab
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Lab
    session_id : int32
    ---
    -> Rig
    """
```

A session belongs to a lab through its primary key and uses a rig, which may belong to another lab, through a secondary foreign key. `Session`'s own `lab_id` and its rig's `lab_id` are independent.

| Table | Columns | Rows |
|---|---|---|
| `Lab` | `lab_id` | 1, 2 |
| `Rig` | `rig_id; lab_id` | (10; 1), (20; 2) |
| `Session` | `lab_id, session_id; rig_id` | (1, 1; 20), (2, 1; 10), (2, 2; 20) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Lab & {"lab_id": 1}` | down | `Lab`: 1<br>`Rig`: 10<br>`Session`: (1, 1), (2, 1) |
| `Session & {"lab_id": 2, "session_id": 1}` | up | `Session`: (2, 1)<br>`Rig`: 10<br>`Lab`: 1, 2 |
| `Rig & {"rig_id": 10}` | both | `Rig`: 10<br>`Session`: (2, 1)<br>`Lab`: 1, 2 |

**Why.** Session (2, 1) belongs to lab 2 but uses rig 10 of lab 1, so it reaches the seed only through `Rig`. `Rig`'s condition, `lab_id = 1`, names an attribute that `Session`'s foreign key to `Rig` does not carry, so it is not copied; `Session` is restricted by the restricted rigs' `rig_id`. Copying it would match sessions on their own `lab_id` and miss session (2, 1), and the DELETE on `Rig` would then fail on its foreign key.

---

## Group shapes

### G1. Part-to-master lift

```python
@schema
class Session(dj.Manual):
    definition = """
    session_id : int32
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_id : int32
        """


@schema
class Review(dj.Manual):
    definition = """
    -> Session
    review_id : int32
    """
```

| Table | Columns | Rows |
|---|---|---|
| `Session` | `session_id` | 1, 2, 3 |
| `Session.Trial` | `session_id, trial_id` | (1, 1), (1, 2), (2, 1), (3, 1) |
| `Review` | `session_id, review_id` | (1, 1), (2, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Session.Trial & {"trial_id": 2}` | down | `Session.Trial`: (1, 1), (1, 2)<br>`Session`: 1<br>`Review`: (1, 1) |
| `Session.Trial & {"trial_id": 2}` | up | `Session.Trial`: (1, 1), (1, 2)<br>`Session`: 1 |

**Why.** The lift selects the sessions that have a matching trial, `Session & (Session.Trial & {"trial_id": 2})`: only session 1. Sessions 2 and 3, and review (2, 1), are untouched. The old upward copy of `trial_id = 2` named no attribute of `Session` and selected every session ([#1591](https://github.com/datajoint/datajoint-python/issues/1591)). Upward, the instance is read whole, so trial (1, 1) comes with trial (1, 2).

The same seed under the other delete modes:

| `part_integrity` | Result |
|---|---|
| `"cascade"` | Deletes the *down* rows above |
| `"ignore"` | Deletes trial (1, 2) only |
| `"enforce"` | Raises before deleting anything: trial (1, 2) would be deleted without session 1 |

### G2. Part-of-part with two chains

```python
@schema
class Ext(dj.Manual):
    definition = """
    ext_id : int32
    """


@schema
class Master(dj.Manual):
    definition = """
    master_id : int32
    """

    class Q(dj.Part):
        definition = """
        -> master
        q_id : int32
        ---
        -> Ext
        """

    class P(dj.Part):
        definition = """
        -> master
        p_id : int32
        ---
        -> Master.Q
        -> Ext
        """
```

`Master.P` is reachable from `Master` through two chains: directly, and through `Master.Q`. Each part also references `Ext`.

| Table | Columns | Rows |
|---|---|---|
| `Ext` | `ext_id` | 1, 2 |
| `Master` | `master_id` | 1, 2, 3 |
| `Master.Q` | `master_id, q_id; ext_id` | (1, 10; 1), (2, 20; 2), (3, 30; 2) |
| `Master.P` | `master_id, p_id; q_id, ext_id` | (1, 100; 10, 2), (2, 200; 20, 1), (3, 300; 30, 2) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Ext & {"ext_id": 1}` | down | `Ext`: 1<br>`Master.Q`: (1, 10), (2, 20)<br>`Master.P`: (1, 100), (2, 200)<br>`Master`: 1, 2 |
| `Master.P & {"master_id": 1, "p_id": 100}` | up | `Master.P`: (1, 100)<br>`Master`: 1<br>`Master.Q`: (1, 10)<br>`Ext`: 1, 2 |

**Why.** Downward, `Ext` 1 reaches Q (1, 10) and P (2, 200), which lift to masters 1 and 2; each master brings its whole instance, and master 3 is untouched. The lift is one step on `master_id`, which every part row carries, so the second chain needs no separate walk. Upward, the instance of P (1, 100) includes Q (1, 10), and the two parts reference `Ext` 1 and 2.

### G3. A second, renamed foreign key to its own master

```python
@schema
class Session(dj.Manual):
    definition = """
    session_id : int32
    """

    class Link(dj.Part):
        definition = """
        -> master
        link_id : int32
        ---
        -> master.proj(other_session="session_id")
        """
```

`Session.Link` belongs to its session through `-> master` (the owning reference, A1) and points to another session through a renamed foreign key.

| Table | Columns | Rows |
|---|---|---|
| `Session` | `session_id` | 1, 2, 3 |
| `Session.Link` | `session_id, link_id; other_session` | (1, 1; 2), (3, 1; 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Session.Link & {"session_id": 1}` | down | `Session.Link`: (1, 1), (3, 1)<br>`Session`: 1, 3 |
| `Session.Link & {"session_id": 1}` | up | `Session.Link`: (1, 1)<br>`Session`: 1, 2 |

**Why.** Link (1, 1) lifts through its owning reference to session 1, not to session 2. Deleting session 1 then deletes link (3, 1), which points to it, and so the rest of instance 3. Upward, link (1, 1) reads session 2, a parent, but not link (3, 1), a child. The renamed foreign key links one instance to another, so this group is [iterated](diagram.md#groups-that-iterate).

With `part_integrity="enforce"`, `(Session & {"session_id": 1}).delete()` raises: it would delete link (3, 1) without session 3.

### G4. Renamed sibling foreign key, chained across three instances

```python
@schema
class Run(dj.Manual):
    definition = """
    run_id : int32
    """

    class Step(dj.Part):
        definition = """
        -> master
        step_id : int32
        """

    class Carry(dj.Part):
        definition = """
        -> master
        carry_id : int32
        ---
        -> Run.Step.proj(prev_run="run_id", prev_step="step_id")
        """
```

A `Carry` row of one run references a `Step` row of an earlier run.

| Table | Columns | Rows |
|---|---|---|
| `Run` | `run_id` | 1, 2, 3, 4 |
| `Run.Step` | `run_id, step_id` | (1, 1), (2, 1), (3, 1), (4, 1) |
| `Run.Carry` | `run_id, carry_id; prev_run, prev_step` | (2, 1; 1, 1), (3, 1; 2, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Run & {"run_id": 1}` | down | `Run`: 1, 2, 3<br>`Run.Step`: (1, 1), (2, 1), (3, 1)<br>`Run.Carry`: (2, 1), (3, 1) |
| `Run & {"run_id": 2}` | down | `Run`: 2, 3<br>`Run.Step`: (2, 1), (3, 1)<br>`Run.Carry`: (2, 1), (3, 1) |
| `Run & {"run_id": 2}` | up | `Run`: 1, 2<br>`Run.Step`: (1, 1), (2, 1)<br>`Run.Carry`: (2, 1) |
| `Run & {"run_id": 2}` | both | `Run`: 1, 2, 3<br>`Run.Step`: (1, 1), (2, 1), (3, 1)<br>`Run.Carry`: (2, 1), (3, 1) |

**Why.** Deleting run 1 deletes step (1, 1), so carry (2, 1), which references it, and so the rest of run 2; that reaches carry (3, 1) and run 3. Run 4 is untouched. One pass over the group would stop at run 1. The engine detects the renamed key and repeats the group step: the master keys grow as {1}, {1, 2}, {1, 2, 3}, and a fourth round adds nothing. Upward the chain runs the other way, from run 2 back to run 1.

### G5. Merge table

```python
@schema
class EphysSource(dj.Manual):
    definition = """
    ephys_id : int32
    """


@schema
class ImagingSource(dj.Manual):
    definition = """
    imaging_id : int32
    """


@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int32
    """

    class Ephys(dj.Part):
        definition = """
        -> master
        ---
        -> EphysSource
        """

    class Imaging(dj.Part):
        definition = """
        -> master
        ---
        -> ImagingSource
        """


@schema
class Analysis(dj.Manual):
    definition = """
    -> Recording
    """
```

`Recording` merges two upstream sources: each recording has one part row, which names its source.

| Table | Columns | Rows |
|---|---|---|
| `EphysSource` | `ephys_id` | 1, 2 |
| `ImagingSource` | `imaging_id` | 1 |
| `Recording` | `recording_id` | 1, 2, 3 |
| `Recording.Ephys` | `recording_id; ephys_id` | (1; 1), (2; 2) |
| `Recording.Imaging` | `recording_id; imaging_id` | (3; 1) |
| `Analysis` | `recording_id` | 1, 2, 3 |

| Seed | Direction | Rows returned |
|---|---|---|
| `Analysis & {"recording_id": 1}` | up | `Analysis`: 1<br>`Recording`: 1<br>`Recording.Ephys`: 1<br>`Recording.Imaging`: none<br>`EphysSource`: 1<br>`ImagingSource`: none |
| `EphysSource & {"ephys_id": 2}` | down | `EphysSource`: 2<br>`Recording.Ephys`: 2<br>`Recording`: 2<br>`Recording.Imaging`: none<br>`Analysis`: 2 |

```python
trace = dj.Diagram.trace(Analysis & {"recording_id": 1})
trace[EphysSource]      # ephys source 1
trace[ImagingSource]    # empty: a node with zero rows, not an error
```

**Why.** Upward, recording 1 brings its whole instance. Its `Ephys` part row references the source that produced the recording, so `trace[EphysSource]` resolves ([#1481](https://github.com/datajoint/datajoint-python/issues/1481)). Downward, deleting ephys source 2 deletes the part row that names it, so the whole of recording 2, and its analysis. With `part_integrity="enforce"` that delete raises, because the part row would go without its master.

### G6. A part violating A1

```python
@schema
class Probe(dj.Manual):
    definition = """
    probe_id : int32
    """

    class Channel(dj.Part):
        definition = """
        -> master.proj(host_id="probe_id")
        channel_id : int32
        """
```

`Probe.Channel` references its master only under a renamed key, so its heading does not contain `probe_id` and it violates A1. Declaring it raises a warning, and it is traversed as a plain table: no lift and no instance.

| Table | Columns | Rows |
|---|---|---|
| `Probe` | `probe_id` | 1, 2 |
| `Probe.Channel` | `host_id, channel_id` | (1, 1), (1, 2), (2, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Probe.Channel & {"host_id": 1, "channel_id": 1}` | down | `Probe.Channel`: (1, 1) |
| `Probe.Channel & {"host_id": 1, "channel_id": 1}` | up | `Probe.Channel`: (1, 1)<br>`Probe`: 1 |
| `Probe & {"probe_id": 1}` | down | `Probe`: 1<br>`Probe.Channel`: (1, 1), (1, 2) |

**Why.** As a plain table, the channel reaches its probe only as a parent: downward nothing lifts, and upward channel (1, 2) is not part of channel (1, 1)'s instance. Deleting the probe still deletes its channels, as children.

---

## Seed shapes

K1 to K6 share one schema:

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    ---
    species : varchar(16)
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_id : int32
    ---
    quality : int32
    """


@schema
class Trial(dj.Manual):
    definition = """
    -> Session
    trial_id : int32
    """


@schema
class Flag(dj.Manual):
    definition = """
    flag_id : int32
    ---
    -> [nullable] Subject
    """
```

| Table | Columns | Rows |
|---|---|---|
| `Subject` | `subject_id; species` | (1; mouse), (2; rat), (3; mouse), (4; rat) |
| `Session` | `subject_id, session_id; quality` | (1, 1; 0), (1, 2; 1), (2, 1; 1), (2, 2; 0), (3, 1; 1) |
| `Trial` | `subject_id, session_id, trial_id` | (1, 1, 1), (1, 2, 1), (2, 1, 1), (2, 2, 1), (3, 1, 1) |
| `Flag` | `flag_id; subject_id` | (1; 1), (2; 3) |

Subject 4 has no sessions.

### K1. Seed restricted by a descendant

| Seed | Direction | Rows returned |
|---|---|---|
| `Subject & (Session & "quality = 0")` | down | `Subject`: 1, 2<br>`Session`: (1, 1), (1, 2), (2, 1), (2, 2)<br>`Trial`: (1, 1, 1), (1, 2, 1), (2, 1, 1), (2, 2, 1)<br>`Flag`: 1 |
| `Subject & (Session & "quality = 0")` | up | `Subject`: 1, 2 |

**Why.** The seed selects subjects 1 and 2, each with a session of quality 0, and *down* takes all their sessions, not only those. The seed's condition reads `Session`, which the delete empties before `Subject`, so the seed is materialized to the keys of subjects 1 and 2 before the first DELETE. Evaluated live, the DELETE on `Subject` would match nothing, and the subjects would remain ([#1496](https://github.com/datajoint/datajoint-python/issues/1496)).

### K2. Self-referencing seed

| Seed | Direction | Rows returned |
|---|---|---|
| `Session & (dj.U("subject_id") & (Session & "quality = 0"))` | down | `Session`: (1, 1), (1, 2), (2, 1), (2, 2)<br>`Trial`: (1, 1, 1), (1, 2, 1), (2, 1, 1), (2, 2, 1) |
| `Session & (dj.U("subject_id") & (Session & "quality = 0"))` | up | `Session`: (1, 1), (1, 2), (2, 1), (2, 2)<br>`Subject`: 1, 2 |

**Why.** The seed selects every session of a subject that has a session of quality 0, and its condition reads `Session` itself, which is deleted no later than the seed. It is materialized before the first DELETE; this also avoids MySQL's refusal of a DELETE whose subquery reads the table being deleted (error 1093).

### K3. Seed kinds give the same rows

Each seed below selects sessions (2, 1) and (2, 2), the sessions of subject 2:

| Kind | Seed |
|---|---|
| dict | `Session & {"subject_id": 2}` |
| list of dicts | `Session & [{"subject_id": 2, "session_id": 1}, {"subject_id": 2, "session_id": 2}]` |
| string | `Session & "subject_id = 2"` |
| string with a subquery | `Session & f"subject_id IN (SELECT subject_id FROM {Subject.full_table_name} WHERE species = 'rat')"` |
| query expression | `Session & (Subject & {"species": "rat"})` |
| `AndList` | `Session & dj.AndList([{"subject_id": 2}, "quality >= 0"])` |
| `Not` | `Session & dj.Not(Flag)`, or `Session - Flag` |

| Seed | Direction | Rows returned |
|---|---|---|
| any of the above | down | `Session`: (2, 1), (2, 2)<br>`Trial`: (2, 1, 1), (2, 2, 1) |
| any of the above | up | `Session`: (2, 1), (2, 2)<br>`Subject`: 2 |
| `Session & dj.Not(Flag)` after inserting `Flag` (3; NULL) | down | `Session`: none<br>`Trial`: none |
| `Session & dj.Not(Flag)` after inserting `Flag` (3; NULL) | up | `Session`: none<br>`Subject`: none |

**Why.** Literal keys cross edges by relabeling and the other kinds cross by restriction; both give the same rows. Upward, only subject 2 is reached, though subject 4 is also a rat, because no selected session references it. The last two rows are the NOT IN NULL trap: `Session & dj.Not(Flag)` compiles to `subject_id NOT IN (SELECT subject_id FROM flag)`, and once that list holds a NULL, SQL's `NOT IN` is never true. The seed then selects no rows, and so does its expansion, in every direction; the materialized form `(Session & dj.Not(Flag)).keys()` is empty too. `expand` takes the rows the database selects for the seed and does not reinterpret its condition.

### K4. `dj.Top` seed

| Seed | Direction | Rows returned |
|---|---|---|
| `Session & "quality = 1" & dj.Top(2)` | down | `Session`: (1, 2), (2, 1)<br>`Trial`: (1, 2, 1), (2, 1, 1) |
| `Session & "quality = 1" & dj.Top(2)` | up | `Session`: (1, 2), (2, 1)<br>`Subject`: 1, 2 |

**Why.** Three sessions have quality 1; `dj.Top(2)` keeps the first two in primary-key order. The `Top` is replaced by those two keys before traversal. Ignoring it would delete session (3, 1) as well ([#1589](https://github.com/datajoint/datajoint-python/issues/1589)).

### K5. Empty seeds

| Seed | Direction | Rows returned |
|---|---|---|
| `Session & False`, `Session & []`, or `Session & {"subject_id": 4}` | down | `Session`: none<br>`Trial`: none |
| the same | up | `Session`: none<br>`Subject`: none |

**Why.** Each seed selects no rows, so each expansion is empty, and the nodes are still present. Subject 4 exists, but no selected session references it: a key dict crosses upward by restriction, not by relabeling, so `{"subject_id": 4}` does not reach it.

### K6. Unrestricted seed

| Seed | Direction | Rows returned |
|---|---|---|
| `Session` | down | `Session`: all five rows<br>`Trial`: all five rows |
| `Session` | up | `Session`: all five rows<br>`Subject`: 1, 2, 3 |
| `Session & {"species": "rat"}` | down, up | The same rows as `Session`, and a warning |

**Why.** An unrestricted seed selects every row. Upward, subject 4 is not reached, because no session references it. `species` is not an attribute of `Session`, so the dict means all rows, as in any restriction. As a seed it raises a warning, because a misspelled attribute would otherwise select every row.

---

## Graph shapes

### X1. Unloaded downstream schema

```python
# module lab.py; the only schema this process activates
lab = dj.Schema("shapes_lab")


@lab
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    """


# module analysis.py; declared earlier, never imported by this process
analysis = dj.Schema("shapes_analysis")


@analysis
class Score(dj.Manual):
    definition = """
    -> Subject
    score_id : int32
    """
```

| Table | Columns | Rows |
|---|---|---|
| `Subject` | `subject_id` | 1, 2 |
| `Score` (in `shapes_analysis`) | `subject_id, score_id` | (1, 1), (2, 1) |

| Seed | Direction | Rows returned |
|---|---|---|
| `Subject & {"subject_id": 1}` | down | `Subject`: 1<br>`Score`: (1, 1) |

**Why.** `expand` first loads every schema that references a loaded schema through foreign keys, so `shapes_analysis` joins the graph even though none of its classes is in scope. Index its table by its full table name.

### X2. Group cycle refused at declaration

```python
@schema
class Session(dj.Manual):
    definition = """
    session_id : int32
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_id : int32
        """


@schema
class Review(dj.Manual):
    definition = """
    -> Session
    """
```

Later, a new part is added to `Session` that references `Review`:

```python
@schema
class Session(dj.Manual):
    definition = """
    session_id : int32
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_id : int32
        """

    class Note(dj.Part):
        definition = """
        -> master
        ---
        -> Review
        """
```

**Result.** Declaring `Session.Note` raises `DataJointError` before any table is created. The message names the part (`Session.Note`), its parent (`Review`), and the cycle: `Session` → `Review` → `Session.Note`, which belongs to `Session`'s group. No rows change.

**Why.** A part may reference its master, a sibling part, or a table whose ancestors, with groups taken whole, do not include its master. `Review` depends on `Session`, so `Session.Note` would make the group its own ancestor: a cycle in the group quotient `Q`. That would make every cascade, trace, and `list_tables()` on the connection fail to order the tables (T8). Two groups whose parts reference each other's masters form the same kind of cycle and are refused the same way.

---

## See also

- [Diagram Specification](diagram.md#traversal-specification) — the definitions these examples follow
- [Cascade Specification](cascade.md) — deletes
- [Upstream Trace Specification](trace.md) — `trace` and `self.upstream`
- [Master-Part Specification](master-part.md) — master-part groups

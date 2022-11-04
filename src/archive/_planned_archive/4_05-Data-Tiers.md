# Table tiers

Table data tiers indicate to database administrators how valuable the
data are. Manual data are the most valuable, as re-entry may be tedious
or impossible. Computed data are safe to delete, as the data can always
be recomputed from within DataJoint. Imported data are safer than manual
data but less safe than computed data because of dependency on external
data sources. With these considerations, database administrators may opt
not to back up computed data, for example, or to back up imported data
less frequently than manual data.

## Table Naming Conventions

On the server side, DataJoint uses a naming scheme to generate a table
name corresponding to a given class. The naming scheme includes prefixes
specifying each table's data tier.

First, the name of the class is converted from `CamelCase` to
`snake_case` ([separation by
underscores](https://en.wikipedia.org/wiki/Snake_case)). Then the name
is prefixed according to the data tier.

> -   `Manual` tables have no prefix.
> -   `Lookup` tables are prefixed with `#`.
> -   `Imported` tables are prefixed with `_`, a single underscore.
> -   `Computed` tables are prefixed with `__`, two underscores.

For example:

The table for the class `StructuralScan` subclassing `dj.Manual` will be
named `structural_scan`.

The table for the class `SpatialFilter` subclassing `dj.Lookup` will be
named `#spatial_filter`.

Again, the internal table names including prefixes are used only on the
server side. These are never visible to the user, and DataJoint users do
not need to know these conventions However, database administrators may
use these naming patterns to set backup policies or to restrict access
based on data tiers.

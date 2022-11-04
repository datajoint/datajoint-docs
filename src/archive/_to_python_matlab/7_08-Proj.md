---
title: Proj
---

Using the `example schema <query-example>`, let table `department` have
attributes **dept**, *dept_name*, *dept_address*, and *dept_phone*. The
primary key attribute is in bold.

Then `department.proj()` will have attribute **dept**.

`department.proj('dept')` will have attribute **dept**.

`department.proj('dept_name', 'dept_phone')` will have attributes
**dept**, *dept_name*, and *dept_phone*.



# Renaming

In addition to selecting attributes, `proj` can rename them. Any
attribute can be renamed, including primary key attributes.

=== "Python"

    This is done using keyword arguments: `tab.proj(new_attr='old_attr')`

=== "Matlab"

    Renaming is done using a string: `tab('old_attr->new_attr')`.

For example, let table `tab` have attributes **mouse**, **session**,
*session_date*, *stimulus*, and *behavior*. The primary key attributes
are in bold.

Then

=== "Python"

    ``` python
    tab.proj(animal='mouse', 'stimulus')
    ```

=== "Matlab"

    ``` matlab
    tab.proj('mouse->animal', 'stimulus')
    ```

will have attributes **animal**, **session**, and *stimulus*.

Renaming is often used to control the outcome of a `join <join>`. For
example, let `tab` have attributes **slice**, and **cell**. Then
`tab * tab` will simply yield `tab`. However,

=== "Python"

    ``` python
    tab * tab.proj(other='cell')
    ```

=== "Matlab"

    ``` matlab
    tab * tab.proj('cell->other')
    ```

yields all ordered pairs of all cells in each slice.

# Calculations

In addition to selecting or renaming attributes, `proj` can compute new
attributes from existing ones.

For example, let `tab` have attributes `mouse`, `scan`, `surface_z`, and
`scan_z`. To obtain the new attribute `depth` computed as
`scan_z - surface_z` and then to restrict to `depth > 500`:

=== "Python"

    ``` python
    tab.proj(depth='scan_z-surface_z') & 'depth > 500'
    ```

=== "Matlab"

    ``` matlab
    tab.proj('scan_z-surface_z -> depth') & 'depth > 500'
    ```


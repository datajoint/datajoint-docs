
=== "Python"

    # Entire table

    The following statement retrieves the entire table as a NumPy
    [recarray](https://docs.scipy.org/doc/numpy/reference/generated/numpy.recarray.html).

    ``` python
    data = query.fetch()
    ```

    To retrieve the data as a list of `dict`:

    ``` python
    data = query.fetch(as_dict=True)
    ```

    In some cases, the amount of data returned by fetch can be quite large;
    in these cases it can be useful to use the `size_on_disk` attribute to
    determine if running a bare fetch would be wise. Please note that it is
    only currently possible to query the size of entire tables stored
    directly in the database at this time.

    # As separate variables

    ``` python
    name, img = query.fetch1('name', 'image')  # when query has exactly one entity
    name, img = query.fetch('name', 'image')  # [name, ...] [image, ...]
    ```

    # Primary key values

    ``` python
    keydict = tab.fetch1("KEY")  # single key dict when tab has exactly one entity
    keylist = tab.fetch("KEY")  # list of key dictionaries [{}, ...]
    ```

    `KEY` can also used when returning attribute values as separate
    variables, such that one of the returned variables contains the entire
    primary keys.

    # Sorting and limiting the results

    To sort the result, use the `order_by` keyword argument.

    ``` python
    # ascending order:
    data = query.fetch(order_by='name')
    # descending order:
    data = query.fetch(order_by='name desc')  
    # by name first, year second:
    data = query.fetch(order_by=('name desc', 'year'))
    # sort by the primary key:
    data = query.fetch(order_by='KEY')
    # sort by name but for same names order by primary key:
    data = query.fetch(order_by=('name', 'KEY desc'))
    ```

    The `order_by` argument can be a string specifying the attribute to sort
    by. By default the sort is in ascending order. Use `'attr desc'` to sort
    in descending order by attribute `attr`. The value can also be a
    sequence of strings, in which case, the sort performed on all the
    attributes jointly in the order specified.

    The special attribute name `'KEY'` represents the primary key attributes
    in order that they appear in the index. Otherwise, this name can be used
    as any other argument.

    If an attribute happens to be a SQL reserved word, it needs to be
    enclosed in backquotes. For example:

    ``` python
    data = query.fetch(order_by='`select` desc')
    ```

    The `order_by` value is eventually passed to the `ORDER BY`
    [clause](https://dev.mysql.com/doc/refman/5.7/en/order-by-optimization.html).

    Similarly, the `limit` and `offset` arguments can be used to limit the
    result to a subset of entities.

    For example, one could do the following:

    ``` python
    data = query.fetch(order_by='name', limit=10, offset=5)
    ```

    Note that an `offset` cannot be used without specifying a `limit` as
    well.

    # Usage with Pandas

    The `pandas` [library](http://pandas.pydata.org/) is a popular library
    for data analysis in Python which can easily be used with DataJoint
    query results. Since the records returned by `fetch()` are contained
    within a `numpy.recarray`, they can be easily converted to
    `pandas.DataFrame` objects by passing them into the `pandas.DataFrame`
    constructor. For example:

    ``` python
    import pandas as pd
    frame = pd.DataFrame(tab.fetch())
    ```

    Calling `fetch()` with the argument `format="frame"` returns results as
    `pandas.DataFrame` objects indexed by the table's primary key
    attributes.

    ``` python
    frame = tab.fetch(format="frame")
    ```

    Returning results as a `DataFrame` is not possible when fetching a
    particular subset of attributes or when `as_dict` is set to `True`.

=== "Matlab"

    DataJoint for MATLAB provides three distinct fetch methods: `fetch`,
    `fetch1`, and `fetchn`. The three methods differ by the type and number
    of their returned variables.

    `query.fetch` returns the result in the form of an *n* ⨉ 1 [struct
    array](https://www.mathworks.com/help/matlab/ref/struct.html) where *n*
    is the number of records matching the query expression.

    `query.fetch1` and `query.fetchn` split the result into separate output
    arguments, one for each attribute of the query.

    The types of the variables returned by `fetch1` and `fetchn` depend on
    the `datatypes <datatypes>` of the attributes. `query.fetchn` will
    enclose any attributes of char and blob types in [cell
    arrays](https://www.mathworks.com/help/matlab/cell-arrays.html) whereas
    `query.fetch1` will unpack them.

    MATLAB has two alternative forms of invoking a method on an object:
    using the dot notation or passing the object as the first argument. The
    following two notations produce an equivalent result:

    ``` matlab
    result = query.fetch(query, 'attr1')
    result = fetch(query, 'attr1')
    ```

    However, the dot syntax only works when the query object is already
    assigned to a variable. The second syntax is more commonly used to avoid
    extra variables.

    For example, the two methods below are equivalent although the second
    method creates an extra variable.

    ``` matlab
    # Method 1
    result = fetch(university.Student, '*');

    # Method 2
    query = university.Student;
    result = query.fetch()
    ```

    # Fetch the primary key

    Without any arguments, the `fetch` method retrieves the primary key
    values of the table in the form of a single column `struct`. The
    attribute names become the fieldnames of the `struct`.

    ``` matlab
    keys = query.fetch;
    keys = fetch(university.Student & university.StudentMajor);
    ```

    Note that MATLAB allows calling functions without the parentheses `()`.

    # Fetch entire query

    With a single-quoted asterisk (`'*'`) as the input argument, the `fetch`
    command retrieves the entire result as a struct array.

    ``` matlab
    data = query.fetch('*');

    data = fetch(university.Student & university.StudentMajor, '*');
    ```

    In some cases, the amount of data returned by fetch can be quite large.
    When `query` is a table object rather than a query expression,
    `query.sizeOnDisk()` reports the estimated size of the entire table. It
    can be used to assess whether running `query.fetch('*')` would be wise.
    Please note that it is only currently possible to query the size of
    entire tables stored directly in the database .

    # As separate variables

    The `fetch1` and `fetchn` methods are used to retrieve each attribute
    into a separate variable. DataJoint needs two different methods to tell
    MATLAB whether the result should be in array or scalar form; for
    numerical fields it does not matter (because scalars are still matrices
    in MATLAB) but non-uniform collections of values must be enclosed in
    cell arrays.

    `query.fetch1` is used when `query` contains exactly one entity,
    otherwise `fetch1` will raise an error.

    `query.fetchn` returns an arbitrary number of elements with character
    arrays and blobs returned in the form of cell arrays, even when `query`
    happens to contain a single entity.

    ``` matlab
    % when tab has exactly one entity:
    [name, img] = query.fetch1('name', 'image');

    % when tab has any number of entities:
    [names, imgs] = query.fetchn('name', 'image');
    ```

    # Obtaining the primary key along with individual values

    It is often convenient to know the primary key values corresponding to
    attribute values retrieved by `fetchn`. This can be done by adding a
    special input argument indicating the request and another output
    argument to receive the key values:

    ``` matlab
    % retrieve names, images, and corresponding primary key values:
    [names, imgs, keys] = query.fetchn('name', 'image', 'KEY');
    ```

    The resulting value of `keys` will be a column array of type `struct`.
    This mechanism is only implemented for `fetchn`.

    # Rename and calculate

    In DataJoint for MATLAB, all `fetch` methods have all the same
    capability as the `proj <proj>` operator. For example, renaming an
    attribute can be accomplished using the syntax below.

    ``` matlab
    [names, BMIs] = query.fetchn('name', 'weight/height/height -> bmi');
    ```

    See `proj` for an in-depth description of projection.

    # Sorting and limiting the results

    To sort the result, add the additional `ORDER BY` argument in `fetch`
    and `fetchn` methods as the last argument.

    ``` matlab
    % retrieve field ``course_name`` from courses
    % in the biology department, sorted by course number
    notes = fetchn(university.Course & 'dept="BIOL"', 'course_name', ...
         'ORDER BY course');
    ```

    The ORDER BY argument is passed directly to SQL and follows the same
    syntax as the [ORDER BY
    clause](https://dev.mysql.com/doc/refman/5.7/en/order-by-optimization.html)

    Similarly, the LIMIT and OFFSET clauses can be used to limit the result
    to a subset of entities. For example, to return the most advanced
    courses, one could do the following:

    ``` matlab
    s = fetch(university.Course, '*', 'ORDER BY course DESC LIMIT 5')
    ```

    The limit clause is passed directly to SQL and follows the same
    [rules](https://dev.mysql.com/doc/refman/5.7/en/select.html)


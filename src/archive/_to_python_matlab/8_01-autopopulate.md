---
title: Auto-populate
---


Imagine that there is a table `test.Image` that contains 2D grayscale
images in its `image` attribute. Let us define the computed table,
`test.FilteredImage` that filters the image in some way and saves the
result in its `filtered_image` attribute.


=== "Python"

    ``` python
    @schema
    class FilteredImage(dj.Computed):
        definition = """ # Filtered image
        -> Image
        ---
        filtered_image : longblob
        """

        def make(self, key):
            img = (test.Image & key).fetch1('image')
            key['filtered_image'] = myfilter(img)
            self.insert1(key)
    ```

    The `make` method receives one argument: the dict `key` containing the
    primary key value of an element of `key source` to be worked
    on.

=== "Matlab"

    ``` MATLAB
    %{ # Filtered image
    -> test.Image
    ---
    filtered_image : longblob
    %}

    classdef FilteredImage < dj.Computed
        methods(Access=protected)
            function make(self, key)
                img = fetch1(test.Image & key, 'image');
                key.filtered_image = myfilter(img);
                self.insert(key)
            end
        end
    end
    ```

    Currently matlab uses `makeTuples` rather than `make`. This will be
    fixed in an upcoming release:
    <https://github.com/datajoint/datajoint-matlab/issues/141>

    The `make` method receives one argument: the struct `key` containing the
    primary key value of an element of `key source` to be worked
    on.


# Populate

The `FilteredImage` table can be populated as

=== "python"

    ``` python
    FilteredImage.populate()
    ```

    The progress of long-running calls to `populate()` in datajoint-python
    can be visualized by adding the `display_progress=True` argument to the
    populate call.

=== "matlab"

    ``` matlab
    populate(test.FilteredImage)
    ```

    Note that it is not necessary to specify which data needs to be
    computed. DataJoint will call `make`, one-by-one, for every key in
    `Image` for which `FilteredImage` has not yet been computed.

# Populate options

=== "python"

    The `populate` method accepts a number of optional arguments that
    provide more features and allow greater control over the method's
    behavior.

    -   `restrictions` - A list of restrictions, restricting as
        `(tab.key_source & AndList(restrictions)) - tab.proj()`. Here
        `target` is the table to be populated, usually `tab` itself.
    -   `suppress_errors` - If `True`, encountering an error will cancel the
        current `make` call, log the error, and continue to the next `make`
        call. Error messages will be logged in the job reservation table (if
        `reserve_jobs` is `True`) and returned as a list. See also
        `return_exception_objects` and `reserve_jobs`. Defaults to `False`.
    -   `return_exception_objects` - If `True`, error objects are returned
        instead of error messages. This applies only when `suppress_errors`
        is `True`. Defaults to `False`.
    -   `reserve_jobs` - If `True`, reserves job to indicate to other
        distributed processes. The job reservation table may be access as
        `schema.jobs`. Errors are logged in the jobs table. Defaults to
        `False`.
    -   `order` - The order of execution, either `"original"`, `"reverse"`,
        or `"random"`. Defaults to `"original"`.
    -   `display_progress` - If `True`, displays a progress bar. Defaults to
        `False`.
    -   `limit` - If not `None`, checks at most this number of keys.
        Defaults to `None`.
    -   `max_calls` - If not `None`, populates at most this many keys.
        Defaults to `None`, which means no limit.

=== "matlab"

    Behavior of the `populate` method depends on the number of output
    arguments requested in the function call. When no output arguments are
    requested, errors will halt population. With two output arguments
    (`failedKeys` and `errors`), `populate` will catch any encountered
    errors and return them along with the offending keys.

# Progress

=== "python"

    The method `table.progress` reports how many `key_source` entries have
    been populated and how many remain. Two optional parameters allow more
    advanced use of the method. A parameter of restriction conditions can be
    provided, specifying which entities to consider. A Boolean parameter
    `display` (default is `True`) allows disabling the output, such that the
numbers of remaining and total entities are returned but not printed.

=== "matlab"

    The function `parpopulate` works identically to `populate` except that
    it uses a job reservation mechanism to allow multiple processes to
    populate the same table in parallel without collision. When running
    `parpopulate` for the first time, DataJoint will create a job
    reservation table and its class `<package>.Jobs` with the following
    declaration:

    ``` matlab
    {%
      # the job reservation table
      table_name      : varchar(255)          # className of the table
      key_hash        : char(32)              # key hash
      ---
      status            : enum('reserved','error','ignore')# if tuple is missing, the job is available
      key=null          : blob                  # structure containing the key
      error_message=""  : varchar(1023)         # error message returned if failed
      error_stack=null  : blob                  # error stack if failed
      host=""           : varchar(255)          # system hostname
      pid=0             : int unsigned          # system process id
      timestamp=CURRENT_TIMESTAMP : timestamp    # automatic timestamp
    %}
    ```

    A job is considered to be available when `<package>.Jobs` contains no
    matching entry.

    For each `make` call, `parpopulate` sets the job status to `reserved`.
    When the job is completed, the record is removed. If the job results in
    error, the job record is left in place with the status set to `error`
    and the error message and error stacks saved. Consequently, jobs that
    ended in error during the last execution will not be attempted again
    until you delete the corresponding entities from `<package>.Jobs`.

    The primary key of the jobs table comprises the name of the class and a
    32-character hash of the job's primary key. However, the key is saved in
    a separate field for error debugging purposes.

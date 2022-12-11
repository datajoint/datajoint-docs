# External Data

# File Attachment Datatype

=== "Matlab"

  Note: External storage is not yet implemented in MATLAB. The feature will be
  added in an upcoming release:
  <https://github.com/datajoint/datajoint-matlab/issues/143>

## Configuration & Usage

Corresponding to issue
[\#480](https://github.com/datajoint/datajoint-python/issues/480), the
`attach` attribute type allows users to <span
class="title-ref">attach</span> files into DataJoint schemas as
DataJoint-managed files. This is in contrast to traditional <span
class="title-ref">blobs</span> which are encodings of programming
language data structures such as arrays.

The functionality is modeled after email attachments, where users <span
class="title-ref">attach</span> a file along with a message and message
recipients have access to a copy of that file upon retrieval of the
message.

For DataJoint `attach` attributes, DataJoint will copy the input file
into a DataJoint store, hash the file contents, and track the input file
name. Subsequent `fetch` operations will transfer a copy of the file to
the local directory of the Python process and return a pointer to it's
location for subsequent client usage. This allows arbitrary files to be
<span class="title-ref">uploaded</span> or <span
class="title-ref">attached</span> to a DataJoint schema for later use in
processing. File integrity is preserved by checksum comparison against
the attachment data and verifying the contents during retrieval.

For example, given a `localattach` store:

``` python
dj.config['stores'] = {
  'localattach': {
    'protocol': 'file',
    'location': '/data/attach'
  }
}
```

A `ScanAttachment` table can be created:

``` python
@schema
class ScanAttachment(dj.Manual):
    definition = """
    -> Session
    ---
    scan_image:    attach@localattach  # attached image scans
    """
```

Files can be added using an insert pointing to the source file:

``` python
>>> ScanAttachment.insert1((0, '/input/image0.tif'))
```

And then retrieved to the current directory using `fetch`:

``` python
>>> s0 = (ScanAttachment & {'session_id': 0}).fetch1()
>>> s0
{'session_id': 0, 'scan_image': './image0.tif'}
>>> fh = open(s0['scan_image'], 'rb')
>>> fh
<_io.BufferedReader name='./image0.tif')
```

# Filepath Datatype

=== "Matlab"

  Note: External storage is not yet implemented in MATLAB. The feature will be
  added in an upcoming release:
  <https://github.com/datajoint/datajoint-matlab/issues/143>

Note: Filepath Datatype is available as a preview feature in DataJoint Python
v0.12. This means that the feature is required to be explicitly enabled.
To do so, make sure to set the [environment
variable](https://en.wikipedia.org/wiki/Environment_variable)
`FILEPATH_FEATURE_SWITCH=TRUE` prior to use.

## Configuration & Usage

Corresponding to issue
[\#481](https://github.com/datajoint/datajoint-python/issues/481), the
`filepath` attribute type links DataJoint records to files already
managed outside of DataJoint. This can aid in sharing data with other
systems such as allowing an image viewer application to directly use
files from a DataJoint pipeline, or to allow downstream tables to
reference data which reside outside of DataJoint pipelines.

To define a table using the `filepath` datatype, an existing DataJoint
`store <external>` should be created and then referenced in the new
table definition. For example, given a simple store:

``` python
dj.config['stores'] = {
  'data': {
    'protocol': 'file',
    'location': '/data',
    'stage': '/data'
  }
}
```

we can define an `ScanImages` table as follows:

``` python
@schema
class ScanImages(dj.Manual):
    definition = """
    -> Session
    image_id:    int
    ---
    image_path:  filepath@data 
    """
```

This table can now be used for tracking paths within the `/data` local
directory. For example:

``` python
>>> ScanImages.insert1((0, 0, '/data/images/image_0.tif'))
>>> (ScanImages() & {'session_id': 0}).fetch1(as_dict=True)
{'session_id': 0, 'image_id': 0, 'image_path': '/data/images/image_0.tif'}
```

As can be seen from the example, unlike `blob <commontypes>` records,
file paths are managed as path locations to the underlying file.

## Integrity Notes

Unlike other data in DataJoint, data in `filepath` records are
deliberately intended for shared use outside of DataJoint. To help
ensure integrity of `filepath` records, DataJoint will record a checksum
of the file data on `insert`, and will verify this checksum on `fetch`.
However, since the underlying file data may be shared with other
applications, special care should be taken to ensure records stored in
`filepath` attributes are not modified outside of the pipeline, or, if
they are, that records in the pipeline are updated accordingly. A safe
method of changing `filepath` data is as follows:

> 1)  Delete the `filepath` database record.
>
>     This will ensure that any downstream records in the pipeline
>     depending on the `filepath` record are purged from the database.
>
> 2)  Modify `filepath` data.
>
> 3)  Re-insert corresponding the `filepath` record.
>
>     This will add the record back to DataJoint with an updated file
>     checksum.
>
> 4)  Compute any downstream dependencies, if needed.
>
>     This will ensure that downstream results dependent on the
>     `filepath` record are updated to reflect the newer `filepath`
>     contents.

### Disable Fetch Verification

Note: Skipping the checksum is not recommended as it ensures file integrity
i.e. downloaded files are not corrupted. With S3 stores, most of the
time to complete a `.fetch()` is from the file download itself as
opposed to evaluating the checksum. This option will primarily benefit
`filepath` usage connected to a local `file` store.

To disable checksums you can set a threshold in bytes for when to stop
evaluating checksums like in the example below:

``` python
dj.config["filepath_checksum_size_limit"] = 5 * 1024**3 # Skip for all files greater than 5GiB
```

The default is `None` which means it will always verify checksums.

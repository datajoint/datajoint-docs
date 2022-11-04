=== "Python"

    In Python, the master-part relationship is expressed by making the part
    a nested class of the master. The part is subclassed from `dj.Part` and
    does not need the `@schema` decorator.

    ``` python
    @schema
    class Segmentation(dj.Computed):
        definition = """ # Different mask segmentations.
        -> Curation
        """

        class Mask(dj.Part):
            definition = """ # A mask produced by segmentation.
            -> master
            mask            : smallint
            ---
            mask_npix       : int       # number of pixels in ROIs
            """

        def make(self, key):
            ...
            self.insert1(key)
            self.Mask.insert(masks)
    ```

=== "Matlab"

    In MATLAB, the master and part tables are declared in a separate
    `classdef` file. The name of the part table must begin with the name of
    the master table. The part table must declare the property `master`
    containing an object of the master.

    `+image/Segmentation.m`

    ``` matlab
    %{
    # Different mask segmentations.
    -> Curation
    %}
    classdef Segmentation < dj.Computed
        methods(Access=protected)
            function make(self, key)
                self.insert(key)
                make(image.SegmentationMask, key)
            end
        end
    end
    ```

    `+image/MotionCorrection.m`

    ``` matlab
    %{
    # Region of interest resulting from segmentation
    -> image.Segmentation
    mask            : smallint
    ---
    mask_npix       : int       # number of pixels in ROIs
    %}

    classdef SegmentationROI < dj.Part
        properties(SetAccess=protected)
            master = image.MotionCorrection
        end
        methods
            function make(self, key)
                ...
                self.insert(entity)
            end
        end
    end
    ```




<!-- TODO: Add link -->

=== "Python"

    ``` python
    @schema
    class MotionCorrection(dj.Imported):
        definition = """  #  Results of motion correction performed
        -> Curation
        ---
        -> scan.Channel.proj(motion_correct_channel='channel') # channel used
        """

        class RigidMotionCorrection(dj.Part):
            definition = """  
            -> master
            ---
            y_shifts            : longblob  # (pixels) y motion correction shifts
            x_shifts            : longblob  # (pixels) x motion correction shifts
            """

        class NonRigidMotionCorrection(dj.Part):
            definition = """
            -> master
            ---
            block_height        : int       # (pixels)
            block_width         : int       # (pixels)
            """

    def make(self, key):
        ...
        self.insert1(key)
        self.RigidMotionCorrection.insert1(rigid_correction)
        self.NonRigidMotionCorrection.insert1(nonrigid_correction)
    ```


=== "Matlab"

    `+image/MotionCorrection.m`
    <!-- TODO: Reviewer, please confirm this matlab -->
    ``` matlab
    %{
    -> image.Curation
    -> scan.Channel.proj(motion_correct_channel='channel')
    %}
    classdef MotionCorrection < dj.Computed
        methods(Access=protected)
            function make(self, key)
                self.insert(key)
                make(image.RigidMotionCorrection, key)
                make(image.NonRigidMotionCorrection, key)
            end
        end
    end
    ```

    `+image/RigidMotionCorrection.m`

    ``` matlab
    %{
    -> image.MotionCorrection
    ---
    y_shifts            : longblob  # (pixels) y motion correction shifts
    x_shifts            : longblob  # (pixels) x motion correction shifts
    %}
    classdef RigidMotionCorrection < dj.Part
        methods(SetAccess=protected)
            function make(self, key)
                ...
                self.insert(rigid_correction)
            end
        end
    end
    ```

    `+image/RigidMotionCorrection.m`

    ``` matlab
    %{
    -> image.MotionCorrection
    ---
    block_height        : int       # (pixels)
    block_width         : int       # (pixels)
    %}
    classdef NonRigidMotionCorrection < dj.Part
        methods(SetAccess=protected)
            function make(self, key)
                ...
                self.insert(nonrigid_correction)
            end
        end
    end
    ```


Conceptually, both rigid and non-rigid motion correction take place in a single motion
correction preprocessing step. Information from both these stages should be entered or
removed together.


## Populating

Master-part relationships can form in any data tier, but DataJoint
observes them more strictly for auto-populated tables. To populate both
the master `Segmentation` and the part `Segmentation.ROI`, it is
sufficient to call the `populate` method of the master:

=== "Python"


=== "Matlab"


Note that the entities in the master and the matching entities in the
part are inserted within a single `make` call of the master, which means
that they are a processed inside a single transactions: 

For example, imagine that a segmentation is performed, but an error
occurs halfway through inserting the results. If this situation were
allowed to persist, then it might appear that 20 ROIs were detected
where 45 had actually been found.

# Deleting

To delete from a master-part pair, one should never delete from the part
tables directly. The only valid method to delete from a part table is to
delete the master. This has been an unenforced rule, but upcoming
versions of DataJoint will prohibit direct deletes from the master
table. DataJoint's `delete <delete>` operation is also enclosed in a
transaction.

Together, the rules of master-part relationships ensure a key aspect of
data integrity: results of computations involving multiple components
and steps appear in their entirety or not at all.

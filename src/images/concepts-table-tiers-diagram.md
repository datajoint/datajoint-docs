<!-- markdownlint-disable MD013 MD041 -->
```mermaid
  flowchart TB
    Mouse --> 
    Session ==> Scan %% Thick line
    Scan --> Alignment((Alignment)) --> Segmentation --> Trace((Trace)) --> RF((RF))
    Scan --> Stimulus --> RF --> Field
    SegmentationMethod -.-> Segmentation((Segmentation)) %% Circle shape
    %% class list,of,nodes class-name
    class Alignment,Mouse,RF,Scan,Segmentation,SegmentationMethod,Session,Stimulus,Trace,Field all;
    class Mouse,Scan,Session,Stimulus manual;
    class Segmentation,Trace,RF compute;
    class SegmentationMethod lookup;
    class Alignment import;
    class Field part;
    %% classDef class-name option1:var1,option2:var2;
    classDef all stroke:#333;   %% Grey stroke around all tables
    classDef manual fill:#060;  %% Green manual tables
    classDef compute fill:#600; %% Red compute tables
    classDef import fill:#006;  %% Blue import tables
    classDef lookup fill:#ddd;  %% Grey lookup tables
    classDef part fill:#FFF;    %% White part tables
    %% Above colors were chosen to be compatible with #00a0df as text
```

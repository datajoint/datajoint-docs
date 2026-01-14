# DataJoint Elements

DataJoint Elements are curated data pipeline modules for neurophysiology experiments.
Each Element implements common patterns for specific data modalities and integrates
seamlessly with other Elements and custom DataJoint pipelines.

For comprehensive documentation, tutorials, and API reference for each Element,
visit the Element's repository.

## Background

DataJoint Elements was developed as part of an NIH [BRAIN Initiative](https://braininitiative.nih.gov/)
project to disseminate open-source data management tools for neuroscience research.

- **Grant:** [U24 NS116470](https://reporter.nih.gov/project-details/10891663) — DataJoint Pipelines for Neurophysiology
- **Institute:** National Institute of Neurological Disorders and Stroke (NINDS)
- **Period:** September 2020 -- August 2025
- **PI:** Dimitri Yatsenko, DataJoint

The project compiled and systematized data pipeline designs from leading neuroscience
laboratories into a library of reusable modules. These modules automate data ingestion
and processing for common experimental modalities including extracellular electrophysiology,
calcium imaging, pose estimation, and optogenetics.

DataJoint Elements is listed in the [BRAIN Initiative Alliance Resource Catalog](https://www.braininitiative.org/toolmakers/resources/datajoint-elements/)
(SciCrunch ID: [SCR_021894](https://scicrunch.org/resolver/SCR_021894)).

## Neurophysiology

<div class="grid cards" markdown>

-   **Element Calcium Imaging**

    ---

    Two-photon and widefield calcium imaging analysis with Suite2p, CaImAn, and EXTRACT.

    [:octicons-arrow-right-24: Documentation](./element-calcium-imaging/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-calcium-imaging)

-   **Element Array Electrophysiology**

    ---

    High-density probe recordings (Neuropixels) with Kilosort and spike sorting.

    [:octicons-arrow-right-24: Documentation](./element-array-ephys/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-array-ephys)

-   **Element Miniscope**

    ---

    Miniscope calcium imaging with UCLA Miniscope and Inscopix systems.

    [:octicons-arrow-right-24: Documentation](./element-miniscope/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-miniscope)

-   **Element Electrode Localization**

    ---

    Anatomical localization of Neuropixels probe electrodes.

    [:octicons-arrow-right-24: Documentation](./element-electrode-localization/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-electrode-localization)

</div>

## Behavior

<div class="grid cards" markdown>

-   **Element DeepLabCut**

    ---

    Markerless pose estimation with DeepLabCut.

    [:octicons-arrow-right-24: Documentation](./element-deeplabcut/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-deeplabcut)

-   **Element Facemap**

    ---

    Orofacial behavior tracking with Facemap.

    [:octicons-arrow-right-24: Documentation](./element-facemap/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-facemap)

-   **Element MoSeq**

    ---

    Behavioral syllable analysis with Keypoint-MoSeq.

    [:octicons-arrow-right-24: Documentation](./element-moseq/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-moseq)

</div>

## Stimulation & Imaging

<div class="grid cards" markdown>

-   **Element Optogenetics**

    ---

    Optogenetic stimulation experiments.

    [:octicons-arrow-right-24: Documentation](./element-optogenetics/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-optogenetics)

-   **Element Visual Stimulus**

    ---

    Visual stimulation with Psychtoolbox.

    [:octicons-arrow-right-24: Documentation](./element-visual-stimulus/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-visual-stimulus)

-   **Element ZStack**

    ---

    Volumetric microscopy with Cellpose segmentation and BossDB integration.

    [:octicons-arrow-right-24: Documentation](./element-zstack/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-zstack)

</div>

## Core Elements

<div class="grid cards" markdown>

-   **Element Lab**

    ---

    Lab, project, and protocol management.

    [:octicons-arrow-right-24: Documentation](./element-lab/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-lab)

-   **Element Animal**

    ---

    Subject and genotype management.

    [:octicons-arrow-right-24: Documentation](./element-animal/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-animal)

-   **Element Session**

    ---

    Experimental session management.

    [:octicons-arrow-right-24: Documentation](./element-session/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-session)

-   **Element Event**

    ---

    Event- and trial-based experiment structure.

    [:octicons-arrow-right-24: Documentation](./element-event/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-event)

-   **Element Interface**

    ---

    Common utilities for DataJoint Elements.

    [:octicons-arrow-right-24: Documentation](./element-interface/)
    [:octicons-mark-github-16: Repository](https://github.com/datajoint/element-interface)

</div>

## Citation

If you use DataJoint Elements in your research, please cite:

> Yatsenko D, Nguyen T, Shen S, Gunalan K, Turner CA, Guzman R, Sasaki M, Sitonic D,
> Reimer J, Walker EY, Tolias AS. [DataJoint Elements: Data Workflows for
> Neurophysiology](https://doi.org/10.1101/2021.03.30.437358). bioRxiv. 2021.

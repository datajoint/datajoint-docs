# Quality Assurance

DataJoint and DataJoint Elements serve as a framework and starting points for numerous
new projects, setting the standard of quality for data architecture and software
design. To ensure higher quality, the following policies have been adopted into the
software development lifecycle (SDLC).

## Coding Standards

When writing code, the following principles should be observed.

- **Style**: Code shall be written for clear readability. Uniform and clear naming
    conventions, module structure, and formatting requirements shall be established
    across all components of the project. Python's 
    [PEP8](https://www.python.org/dev/peps/pep-0008/#naming-conventions) standard offers
    clear guidance to this regard which can similarly be applied to all languages.
  - Python code is formatted with the [black](https://github.com/psf/black) code formatter.
  - Line length should be a maximum of 88 characters.

- **Maintenance Overhead**: Code base size should be noted to prevent large,
    unnecessarily complex solutions from being introduced. The idea is that the larger
    the code base, the more there is to review and maintain. Therefore, we should aim
    to find a compromise where we can keep the code base from becoming too large
    without adding convoluted complexity.

- **Performance**: Performance drawbacks should be avoided, controlled, or, at least, be
    properly monitored and justified. For instance: memory management, garbage
    collection, disk reads/writes, and processing overhead should be regarded to ensure
    that an efficient solution is achieved.

## Automated Testing

All components and their revisions must include appropriate automated software testing
to be considered for release. The core framework must undergo thorough performance
evaluation and comprehensive integration testing.

Generally, this includes tests related to:

- **Syntax**: Verify that the code base does not contain any syntax errors and will run
    or compile successfully.

- **Unit & Integration**: Verify that low-level, method-specific tests (unit tests) and
    any tests related coordinated interface between methods (integration tests) pass
    successfully. Typically, when bugs are patched or features are introduced, unit and
    integration tests are added to ensure that the use-case intended to be satisfied is
    accounted for. This helps us prevent any regression in functionality.

- **Style**: Verify that the code base adheres to style guides for optimal readability.

- **Code Coverage**: Verify that the code base has similar or better code coverage than
    the last run.

## Code Reviews

When introducing new code to the code base, the following will be required for
acceptance by DataJoint core team into the main code repository.

- **Independence**: Proposed changes should not directly alter the code base in the
  review process. New changes should be applied separately on a copy of the code base
  and proposed for review by the DataJoint core team. For example, apply changes on a
  GitHub fork and open a pull request targeting the `main` branch once ready for review.

- **Etiquette**: An author who has requested for a code for review should not accept and
    merge their own code to the code base. A reviewer should not commit any suggestions
    directly to the authors proposed changes but rather should allow the author to
    review.

- **Coding Standards**: Ensure the above coding standards are respected.

- **Summary**: A description should be included that summarizes and highlights the
    notable changes that are being proposed.

- **Issue Reference**: Any bugs or feature requests that have been filed in the issue
    tracker that would be resolved by acceptance should be properly linked and
    referenced.

- **Satisfy Automated Tests**: All automated tests associated with the project will be
  verified to be successful prior to acceptance.

- **Documentation**: Documentation should be included to reflect any new feature or
    behavior introduced.

- **Release Notes**: Include necessary updates to the release notes or change log to
    capture a summary of the patched bugs and new feature introduction. Proper linking
    should be maintained to associated tickets in issue tracker and reviews.

## Release Process

Upon satisfactory adherence to the above Coding Standards, Automated Testing, and Code
Reviews:

- The package version will be incremented following the standard definition of
  [Semantic Versioning](https://semver.org/spec/v2.0.0.html) with a `Major.Minor.Patch`
  number.

- Updates will be merged into the base repository `main` branch.

- A new release will be made on PyPI.

For external research teams that reach out to us, we will provide engineering support to
help users adopt the updated software, collect feedback, and resolve issues following
the processes described in the section below. If the updates require changes in the
design of the database schema or formats, a process for data migration will be provided
upon request.

## User Feedback & Issue Tracking

All components will be organized in GitHub repositories with guidelines for
contribution, feedback, and issue submission to the issue tracker. For more information
on the general policy around issue filing, tracking, and escalation, see the
[DataJoint Open-Source Contribute](../../../community/contribute) policy. For
research groups that reach out to us, our team will work closely to collect feedback
and resolve issues. Typically issues will be prioritized based on their criticality and
impact. If new feature requirements become apparent, this may trigger the creation of a
separate workflow or a major revision of an existing workflow.

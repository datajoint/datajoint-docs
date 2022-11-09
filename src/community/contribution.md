# Contribution Guidelines

Thank you for your interest in contributing! 🤝

To help keep everyone in alignment and coordinated in the community effort, we’ve
created this document. It serves as the contribution guideline that outlines how
open-source software development is to be conducted. Any software development that makes
reference to this document can be assumed to adopt the policies outlined below. We’ve
structured the guideline in a FAQ (frequently asked questions) format to make it easier
to digest. Feel free to review the questions below to determine any specific policy.

The principal maintainer of DataJoint and associated tools is the DataJoint company. The
pronouns “we” and “us” in this guideline refer to the principal maintainers. We invite
reviews and contributions of the open-source software. We compiled these guidelines to
make this work clear and efficient.

## Feedback

DataJoint APIs, DataJoint Web GUIs, and DataJoint Elements are supported by NIH grant
U24 NS116470 for disseminating open-source software for neuroscience research. Your
feedback is essential for continued funding. Your feedback also helps shape the
technology development roadmap for the DataJoint ecosystem. Please tell us about your
projects by filling out the [DataJoint Census](https://community.datajoint.io).

## 1) Which issue should I contribute towards?

There are three primary things to consider when looking to contribute.

**Availability:** An indication of whether anyone is currently working on a fix for the
given issue. Availability is indicated by who is `assigned`. Issues that are
`unassigned` mean that there is no one yet working on resolving the issue and the issue
is available for someone to work on. If an issue has been assigned, then any additional
work on that issue should be coordinated with the assignee.

**Specification:** In order for issues to be properly addressed, the requirements of
satisfying and closing the issue should be clear. If it is not, a label will be added as
`unspecified`. This could be due to more debug info being necessary, more details on
intended behavior, or perhaps that further discussion is required to determine a good
solution. Feel free to help us arrive at a proper specification.

**Priority:** As a community, we work on a concerted effort to bring about the
realization of the milestones. We utilize milestones as a planning tool to help focus a
group of changes around a release. To determine the priority of issues, simply have a
look at the next milestone that is expected to arrive. Therefore, each milestone
following this can be understood as lower in priority respectively. Bear in mind that
much like a hurricane forecast, the execution plan is much more likely to be accurate
the closer to today’s date as opposed to milestones further out. Extremely low priority
issues are assigned to the `Backburner` milestone. Since `Backburner` does not have a
target date, this indicates that its issues may be deferred indefinitely. Occasionally
the maintainers will move issues from `Backburner` as it makes sense to address them
within a release. Also, issues `unassigned` to a milestone can be understood as new
issues which have not been triaged.

After considering the above, you may comment on the issue you’d like to help fix and a maintainer will assign it to you.

## 2) What is the proper etiquette for proposing changes as contribution?

What is generally expected from new contributions are the following:

Any proposed contributor changes should be introduced in the form of a pull request (PR)
from their fork.

Proper branch target specified. The following are the generally the available branches
that can be targeted:

- `main` or `master`: Represents the single source of truth and the latest in completed development.

- `pre`: Represents the source at the point of the last stable release.

For larger more involved changes, a maintainer may determine it best to create a
feature-specific branch and adjust the PR accordingly.

A summary description that describes the overall intent behind the PR.

Proper links to the issue(s) that the PR serves to resolve.

Newly introduced changes must pass any required checks. Typically as it relates to tests, this means:

1. No syntax errors
1. No integration errors
1. No style errors e.g. PEP8, etc.
1. Similar or better code coverage

Additional documentation to reflect new feature or behavior introduced.

Necessary updates to the changelog following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
convention.

A contributor should not approve or merge their own PR.

Reviewer suggestions or feedback should not be directly committed to a branch on a
contributor’s fork. A less intrusive way to collaborate would be for the reviewer to PR
to the contributor’s fork/branch that is associated with the main PR currently in
review.

Maintainers will also ensure that PR’s have the appropriate assignment for reviewer, milestone, and project.

## 3) How can I track the progress of an issue that has been assigned?

Since milestones represent the development plan, projects represent the actual
execution. Projects are typically fixed-time sprints (1-2 weeks). A ‘workable’ number of
issues that have been assigned to developers and assigned to the next milestone are
selected and tracked in each project to provide greater granularity in the week-to-week
progress. Automation is included observing the `Automated kanban with reviews` template.
Maintainers will adjust the project assignment to reflect the order in which to resolve
the milestone issues.

## 4) What is the release process? How do I know when my merged contribution will officially make it into a release?

Releases follow the standard definition of [semantic versioning](https://semver.org/spec/v2.0.0.html).
Meaning:

`MAJOR` . `MINOR` . `PATCH`

- `MAJOR` version when you make incompatible API changes,

- `MINOR` version when you add functionality in a backwards compatible manner, and

- `PATCH` version when you make backwards compatible bug fixes.

Each release requires tagging the commit appropriately and is then issued in the normal
medium for release e.g. PyPi, NPM, YARN, GitHub Release, etc.

Minor releases are triggered when all the issues assigned to a milestone are resolved
and closed. Patch releases are triggered periodically from `main` or `master` after a
reasonable number of PR merges have come in.

## 5) I am not yet too comfortable contributing but would like to engage the community. What is the policy on community engagement?

In order to follow the appropriate process and setting, please reference the following flow for your desired mode of engagement:

### 5a) Generally, how do I perform __________?

If the documentation does not provide clear enough instruction, please see StackOverflow
posts related to the [datajoint](https://stackoverflow.com/questions/tagged/datajoint)
tag or ask a new question tagging it appropriately. You may refer to our 
[datajoint tag wiki](https://stackoverflow.com/tags/datajoint/info)
for more details on its proper use.

### 5b) I just encountered this error, how can I resolve it?

Please see StackOverflow posts related to the 
[datajoint](https://stackoverflow.com/questions/tagged/datajoint) tag or ask a new 
question tagging it appropriately. You may refer to our 
[datajoint tag wiki](https://stackoverflow.com/tags/datajoint/info) for more details on
its proper use.

### 5c) I just encountered this error and I am sure it is a bug, how do I report it?

Please file it under the issue tracker associated with the open-source software.

### 5d) I have an idea or new feature request, how do I submit it?

Please file it under the issue tracker associated with the open-source software.

### 5e) I am curious why the maintainers choose to __________? i.e. questions that are ‘opinionated’ in nature with answers that some might disagree.

Please join the community on the 
[DataJoint Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE)
and ask on the most relevant channel. There, you may engage directly with the maintainers for proper discourse.

### 5f) What is the timeline or roadmap for the release of certain supported features?

Please refer to milestones and projects associated with the open-source software.

### 5g) I need urgent help best suited for live debugging, how can I reach out directly?

Please join the community on the 
[DataJoint Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE)
and ask on the most relevant channel. Please bear in mind that as open-source community software, availability of the maintainers might be limited.

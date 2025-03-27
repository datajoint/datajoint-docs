# Contribution Guidelines

Thank you for your interest in contributing to DataJoint open-source software!

These guidelines are designed to ensure smooth collaboration, high-quality contributions, and a welcoming environment for all contributors. Please take a moment to review this document in order to make the contribution process easy and effective for everyone involved.

The principal maintainer of DataJoint and associated tools is the DataJoint company. The pronouns “we” and “us” in this guideline refer to the principal maintainers. We invite reviews and contributions of the open-source software. We compiled these guidelines to make this work clear and efficient.

## Table of Contents
- [Community Engagement](#community-engagement)
- [How to Contribute](#how-to-contribute)
  - [Project Lists](#project-lists)
  - [Prerequisites](#prerequisites)
  - [Reporting Bugs](#reporting-bugs)
  - [Proposing Features or Enhancements](#proposing-features-or-enhancements)
  - [Submitting Pull Requests (PRs)](#submitting-pull-requests-prs)
  - [Code Reviews](#code-reviews)
- [Releases](#releases)
- [Contribution Acknowledgment](#contribution-acknowledgment)


## Community Engagement

For general questions, ideas, discussions or live debugging sessions, please join [DataJoint Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE) or [Stack Overflow](https://stackoverflow.com/questions/tagged/datajoint), but for direct technical issues should stay in `Github Issue` in the respective project's repository. Response times may vary depending on maintainer availability.

- For resolving bugs, errors, or general debugging help, please submit it through `Github Issue` in the respective repository.
- For live debugging, urgent help, or broader discussions, join the [DataJoint Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE).
- For feature requests, please open an issue directly in the `Github Issue` of the respective repository providing sufficient details to facilitate discussion and prioritization.

[Back to Top](#table-of-contents)

## How to Contribute

### Project Lists

Actively maintained projects by DataJoint:

- DataJoint Enhancement Proposal - in progress
- [DataJoint Specs](https://github.com/datajoint/datajoint-specs)
- [DataJoint Docs](https://github.com/datajoint/datajoint-docs)
  - It is the landing page of DataJoint documentation.
  - Each project has its own documentation in its repository.
  - Please help us to improve our documetations, it's the easiest but most impactful way to contribute!
- [DataJoint Python](https://github.com/datajoint/datajoint-python)
- [DataJoint Elements](https://github.com/orgs/datajoint/repositories?q=element)
- [datajoint/djlabhub-docker](https://github.com/datajoint/djlabhub-docker)
- [datajoint/nginx-docker](https://github.com/datajoint/nginx-docker)

Archived projects by DataJoint, but still open for community contributions:

- [Datajoint MATLAB](https://github.com/datajoint/datajoint-matlab)
- [DataJoint Pharus](https://github.com/datajoint/pharus)
- [DataJoint SciViz](https://github.com/datajoint/sci-viz)
- [DataJoint LabBook](https://github.com/datajoint/datajoint-labbook)
- Most of [Docker images](https://github.com/orgs/datajoint/repositories?q=docker) expect the ones listed above

### Prerequisites

- Familiarize yourself with the project documentation and guidelines.
- Start with reading the repository's `README.md` and `CONTRIBUTION.md`. You should expect to find the following instructions for the respective project:
    - Installation instructions.
    - Development environment setup.
    - Testing instructions.

> Please open an issue in the respective repository if any of those instructions in the documentations or `READMD.md` are unclear to you. Contributions to documentations are equivalently important to any code for the community, please help us to resolve any confusions in documentations.

### Reporting Bugs

Before you open up a new issue, please check `Github Issue` to see if there are any related open/closed issues or open/closed PRs to avoid duplicates. If not, please open a new issue with clearly description of your bug, including:

- Steps to reproduce (if applicable).
- Expected and actual outcomes.
- Any relevant error messages, logs, or screenshots.
- Include environment details (e.g., OS, pip, conda dependencies) to speed up troubleshooting.

### Proposing Features or Enhancements

Before starting your significant work, open a `Github Issue` to discuss your proposal first. Please include:

- A clear problem statement.
- Proposed solution or feature details.
- Relevant examples or use cases.

> There will be a repository for DataJoint Enhancement Proposal to centralize all proposals, it is currently in progress.

### Submitting Pull Requests (PRs)

> In DataJoint, we use **[Forking Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow)** to manage contributions to keep the main fork's branch management clean.

1. Fork the repository to your own Github account and clone it to your local machine.
    - Please remember to always sync your fork's main branch with the DataJoint repository's main branch before starting your work.
    - In your own fork, we suggest you use [Feature Branch Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow) to manage your branches in your own fork, just in case someone will work on multiple contributions at the same time.
2. Create a descriptive feature/fix branch from your fork's main branch, e.g., `fix/typo-docs` or `feature/add-logging`.
3. Optionally, but highly recommended to follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) to make commit messages easier to be searched and categorized: If you use VSCode, please install [Conventional Commits](https://marketplace.visualstudio.com/items?itemName=vivaxy.vscode-conventional-commits) extention, it will help you to edit your commit messages following the commit types for versioning:
    - `fix`: Bug fixes.
    - `feat`: New features.
    - `docs`: Documentation updates.
    - `Breaking changes`: Changes would break backward compatibility, may affect the existing users when they upgrade. Use ! after the type or add BREAKING CHANGE in the commit footer.
    - `chore`: Like the name, it is a chore.
    - Example, if you are not using the VSCode extension: `git commit -m "fix(auth): resolve token expiration bug."`
4. Reference related issue(s) in your PR description (e.g., Closes #123).
5. Cover new functionality or bug fixes with appropriate tests. Ensure all tests pass before submission. Typically as it relates to tests, this means:
   1. No syntax errors
   2. No integration errors
   3. No style errors e.g. PEP8, etc.
   4. Similar or better code coverage
6. **Additional documentation** to reflect new feature or behavior introduced.
7. Provide a detailed PR description explaining the changes and their impact.
8. Submit the PR for review. Maintainers will also ensure that PR’s have the appropriate assignment for reviewer.

### Code Reviews

A contributor should not approve or merge their own PR. A maintainer will review and
approve the PR.

Reviewer suggestions or feedback should not be directly committed to a branch on a
contributor’s fork. A less intrusive way to collaborate would be for the reviewer to PR
to the contributor’s fork/branch that is associated with the main PR currently in
review.

Expect constructive feedback from maintainers. Maintainers will review your PR and suggest changes or improvements. Be responsive to feedback and iterate as needed. Reviews focus on code quality and adherence to standards, and documentation and test coverage. Once approved, the PR will be merged.

[Back to Top](#table-of-contents)

## Releases

Releases follow the standard definition of
[semantic versioning](https://semver.org/spec/v2.0.0.html). Meaning:

`MAJOR` . `MINOR` . `PATCH/MICRO`

- `MAJOR` version bump when breaking changes make backward incompatible.

- `MINOR` version bump when added functionalities is backward compatible.

- `PATCH/MICRO` version when included bug fixes are backward compatible.

> Backward Compatible means that the existing users can upgrade to the new version without any changes to their existing code.

For DataJoint open-source projects, we have two ways of making a release at this moment since we are improving the release process, and we will eventually consolidate into one way:

- Datajoint Python release, the future direction:
  - We use `Github Label` and [PR Labeler action](https://github.com/actions/labeler) to categorize each PR.
  - Then we use [Release Drafter](https://github.com/release-drafter/release-drafter) to manually trigger a Github Actions workflow to make a draft release.
  - Changelog will be provided by [Github Compare URL](https://github.com/datajoint/datajoint-python/compare/v0.14.2...v0.14.3) at the end of the release note.
  - Then we manually publish the draft release to trigger a release Github Actions workflow.
- Others:
  - This process is very dependent on conventional commits and tagging.
  - It will be triggered by pushing a new tag to the repository.
  - It uses [python-semantic-release](https://python-semantic-release.readthedocs.io/en/latest/) to parse all the conventional commits for the release note and `CHANGELOG.md`.

> We found the former resolver would work the best for our community since contributors are from different background, we do not want to require them to adopt conventional commits.

[Back to Top](#table-of-contents)

## Contribution Acknowledgment

We deeply appreciate every contribution! By adhering to these guidelines, you help maintain the quality, usability, and success of any DataJoint open-source software.

For any questions, feel free to reach out via `Github Issue` in the specific repository, our [Community Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE) or contact `support@datajoint.com`.

Thank you for your contributions!

[Back to Top](#table-of-contents)

# Contribution Guidelines

Thank you for your interest in contributing to DataJoint Elements!

These guidelines are designed to ensure smooth collaboration, high-quality
contributions, and a welcoming environment for all contributors. Please take a moment to
review this document in order to make the contribution process easy and effective for
everyone involved.

The principal maintainer of DataJoint and associated tools is the DataJoint company. The
pronouns “we” and “us” in this guideline refer to the principal maintainers. We invite
reviews and contributions of the open-source software. We compiled these guidelines to
make this work clear and efficient.

## How to Contribute

### Feedback and Communication

Engage with the community through GitHub Issues and PR discussions.

Use inclusive and professional language.

For general questions or ideas, discussions and live debugging support, please join
[DataJoint Slack channel](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE)
or [other community forums](https://stackoverflow.com/questions/tagged/datajoint), but
direct technical contributions should stay in GitHub. Response times may vary depending
on maintainer availability.

### Reporting Issues

Use `GitHub Issues` to report bugs or request features. Clearly describe the issue,
including:

- Steps to reproduce (if applicable).
- Expected and actual outcomes.
- Any relevant error messages, logs, or screenshots.
- Include environment details (e.g., OS, library versions) to speed up troubleshooting.

Check existing issues to avoid duplicates.

### Proposing Features/Changes

Before significant contributions, open a `GitHub Issue` to discuss your proposal. Please
include:

- A clear problem statement.
- Proposed solution or feature details.
- Relevant examples or use cases.

### Submitting Pull Requests (PRs)

1. Fork the repository and clone it to your local machine.
2. Create a descriptive branch name, e.g., `fix/typo-docs` or `feature/add-logging`.
3. Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): Use
   commit messages following the commit types for versioning:

- `fix`: Bug fixes (PATCH in Semantic Versioning).
- `feat`: New features (MINOR in Semantic Versioning).
- `docs`: Documentation updates.
- `Breaking changes`: Use ! after the type or add BREAKING CHANGE in the commit footer.

- `Example: fix(auth): resolve token expiration bug.`

4. Reference related issue(s) in your PR description (e.g., Closes #123).
5. Cover new functionality or bug fixes with appropriate tests. Ensure all tests pass
   before submission. Typically as it relates to tests, this means:
   1. No syntax errors
   2. No integration errors
   3. No style errors e.g. PEP8, etc.
   4. Similar or better code coverage
6. Additional documentation to reflect new feature or behavior introduced.
7. Provide a detailed PR description explaining the changes and their impact.
8. Submit the PR for review. Maintainers will also ensure that PR’s have the appropriate
   assignment for reviewer.

A contributor should not approve or merge their own PR. A maintainer will review and
approve the PR.

Reviewer suggestions or feedback should not be directly committed to a branch on a
contributor’s fork. A less intrusive way to collaborate would be for the reviewer to PR
to the contributor’s fork/branch that is associated with the main PR currently in
review.

### Code Reviews

Expect constructive feedback from maintainers. Maintainers will review your PR and
suggest changes or improvements. Be responsive to feedback and iterate as needed.
Reviews focus on code quality and adherence to standards, and documentation and test
coverage. Once approved, the PR will be merged.

## Releases

Releases follow the standard definition of
[semantic versioning](https://semver.org/spec/v2.0.0.html). Meaning:

`MAJOR` . `MINOR` . `PATCH`

- `MAJOR` version when you make incompatible API changes,

- `MINOR` version when you add functionality in a backwards compatible manner, and

- `PATCH` version when you make backwards compatible bug fixes.

Each release requires tagging the commit appropriately and is then issued following the
GitHub automated semantic release. The release and Changelog will be generated
automatically after the PR is merged.

## Community Engagement

- For resolving bugs, errors, or debugging issues, please submit it through **GitHub
  Issues**.
- For live debugging, urgent help, or broader discussions, join the
  [DataJoint Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE).
  Keep in mind maintainers’ availability may be limited.
- For feature requests, directly in the GitHub Issue Tracker of the respective
  repository Provide sufficient details to facilitate discussion and prioritization.

## Prerequisites

- Familiarize yourself with the project documentation and guidelines.
- Install necessary tools and dependencies listed in the repository's `README`.

## Contribution Acknowledgment

We deeply appreciate every contribution! By adhering to these guidelines, you help
maintain the quality, usability, and success of DataJoint Elements.

For any questions, feel free to reach out via GitHub Issues, our
[community Slack](https://join.slack.com/t/datajoint/shared_invite/enQtMjkwNjQxMjI5MDk0LTQ3ZjFiZmNmNGVkYWFkYjgwYjdhNTBlZTBmMWEyZDc2NzZlYTBjOTNmYzYwOWRmOGFmN2MyYzU0OWQ0MWZiYTE)
or contact `support@datajoint.com`.

Thank you for your contributions!

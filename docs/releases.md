# Release lifecycle

Releases are versioned snapshots of the CLI, catalog and image recipes.
Docker images are built locally using each project's configuration.
`VERSION` is the single source of the application version; each published
version has an annotated `vX.Y.Z` tag, a changelog section and a GitHub Release.

## Version selection

The maintainer selects a `patch`, `minor` or `major` increment when
triggering **Prepare release** on `main`. Commit types determine changelog
categories, not version increments.

| Increment | Expected changes | Examples in roke |
|---|---|---|
| Major | Incompatible changes that require users to adapt commands, configuration or workflows. | Removing a command, renaming a setting without compatibility, or changing a default that requires migration. |
| Minor | New functionality that preserves existing usage. | Adding a command, an optional flag, or support for a new service or agent. |
| Patch | Compatible fixes and maintenance, without new functionality. | Fixing argument parsing, correcting documentation, or updating dependencies without changing supported usage. |

Breaking changes use a minor increment below `1.0.0` and a major increment
from `1.0.0` onward. Their commits carry `!` and a `BREAKING CHANGE:` footer
with migration instructions, following the repository's commit conventions.

## Release preparation

`.github/workflows/prepare-release.yml` runs `scripts/release.py prepare`
against `main`. It updates `VERSION` and generates a section in
`CHANGELOG.md`, then commits those files with a sign-off to `release/next`
and opens or updates its PR. That branch is reserved for generated release
metadata; code changes belong in separate PRs.

The changelog lists non-merge commits since the previous release recorded
in its history. Entries are grouped by type and link to their commits;
breaking changes and migration instructions appear first. Administrative
release commits are omitted. A comparison link identifies the release's
complete range of changes.

Preparation records the source commit in a comment in the changelog.
Repeated preparation regenerates the notes from the current `main` and
updates the same PR, replacing edits to generated notes.

## Validation

CI checks that the version matches the changelog, that commit links cover
the release range and that no code changes arrived after the recorded
source commit. A release PR contains only `VERSION` and `CHANGELOG.md`.
If `main` advances while the PR is open, preparation must run again before
merging.

The preparation workflow explicitly dispatches CI for the generated branch.
Publication is a final CI job, dependent on both the normal checks and the
real Docker tests. Only pushes to `main` can publish; the tag references the
exact commit tested by that run.
Publication requires pending release metadata; ordinary contributions do
not create a release on their own.

## Publication and recovery

`.github/workflows/publish-release.yml` calls `scripts/release.py publish`.
It creates the annotated tag and a draft GitHub Release, uploads `install.sh`
and `SHA256SUMS`, then publishes the release as the latest stable version.
GitHub supplies source archives for the tag. Release notes match the section
committed to `CHANGELOG.md`.

Publication is retryable from the same CI run. An interrupted upload leaves
a draft, and a retry replaces incomplete draft assets before publishing.
Already published releases are left unchanged. Existing tags are never
moved to another commit, and an older release cannot replace a newer one
as the latest stable release.

An unpublished version whose notes are stale can be refreshed with patch
preparation, retaining its version number. This recovery applies before
a tag has been created. Once a tag exists, the original publication run
must finish before preparing another release.

## Implementation and tests

`scripts/release.py` uses standard-library Python, Git and the GitHub CLI.
Preparation requires a clean checkout with full history and tags; its
output notes file must be outside the checkout so it does not make the
working tree dirty.

```bash
python3 scripts/release.py prepare --bump patch \
  --repository bameda/roke --notes-file /tmp/roke-release-notes.md
git diff -- VERSION CHANGELOG.md
```

Preparation edits files without committing or publishing. Verification
runs against committed release metadata. The tests exercise version
selection, changelog coverage, stale notes, tag conflicts, draft publication
and retries using local repositories and a fake GitHub CLI.

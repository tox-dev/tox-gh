# Contributing

Add a `changelog.d/+short-name.<category>.md` fragment for each user-visible change. Use a descriptive name instead of a
pull request number. After a squash merge, the release workflow links the fragment to the pull request. A pull request
with two separate user-visible changes needs two fragments.

Do not write credits in fragments. The release credits come from the commit authors and `Co-authored-by` trailers, and
the prepare workflow runs `release-creator contributors` to add first-time contributors to the changelog.

Use these categories:

| Fragment suffix | Changelog heading | Use for                                                   |
| --------------- | ----------------- | --------------------------------------------------------- |
| `feature`       | Added             | New capabilities and Python support additions or removals |
| `change`        | Changes           | Changes to existing behavior                              |
| `bugfix`        | Fixed             | User-visible fixes                                        |
| `doc`           | Documentation     | User documentation changes                                |
| `breaking`      | Breaking changes  | Incompatible changes to the public interface              |
| `security`      | Security          | Security fixes users should know about                    |
| `performance`   | Performance       | User-visible speed or resource improvements               |
| `deprecation`   | Deprecated        | Public features scheduled for removal                     |
| `removal`       | Removed           | Removed public features other than Python support         |
| `packaging`     | Packaging         | Distribution or installation changes                      |

For example, `changelog.d/+runner-selection.feature.md` could contain:

```markdown
Select the matching tox environment for free-threaded Python 3.15.
```

Internal maintenance needs no fragment. Apply the `skip news` label to a human-authored maintenance pull request; the
bot labeling workflow handles supported automation. A bot-supplied fragment is kept.

To preview pending news locally, install the locked release tools and let the fragments select the next version:

```bash
uv venv --python 3.15 .tox/release-tools
uv pip sync --preview-features pylock --python .tox/release-tools/bin/python --group release-news pylock.toml
version=$(git tag --list | .tox/release-tools/bin/release-creator tags --next auto --directory changelog.d)
.tox/release-tools/bin/towncrier build --draft --version "$version"
```

The draft shows named fragments before merge. The final changelog gains pull request links after the squash commit is on
`main`, and the prepare workflow adds the credits.

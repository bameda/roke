## What and why

<!-- What this pull request changes, and why. Link the issue it closes: "Closes #123". -->

## How it was tested

<!-- The commands you ran, and on what (distribution, agent, services). -->

## Checklist

- [ ] Tests cover the change (`uvx pytest` passes)
- [ ] `uvx pre-commit run --all-files` passes
- [ ] The documentation is updated, if the change affects how roke is used
- [ ] Commits follow Conventional Commits; a change that requires users to
      do something is marked with `!` and explains what to do in a
      `BREAKING CHANGE:` paragraph

## Security

<!-- roke keeps the agent away from everything but the project. -->

- [ ] This change does not widen what the box can reach (mounts,
      capabilities, network, guards)
- [ ] It does, and the description above explains why it is needed

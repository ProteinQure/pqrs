## Versioned roles

In order to accelerate the PQRS update runs, we'd like to avoid re-running
roles if they were not updated.

Potential solutions:
1) Tracking the changes to the collection using VCS, like git
2) Explicitly versioning each role with a semantic version

### Decision: Use explicitly versioned roles

While using git to track changes to roles is appealing, because it does not
impose any additional overhead on the collection maintainers, it can lead to
imperfect results.

We can use our VCS to obtain a list of directories (roles) modified between two
commits (last commit using which update was performed on this computer, and the
latest commit). However, some roles could end up on this list by accident - the
modifications to their content might be purely cosmetic (whitespace changes) or
could be of such nature that do not require re-running the roles (removing
tasks).

Therefore the project will proceed with explicit versioning of the roles.

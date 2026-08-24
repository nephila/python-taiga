Ship a ``py.typed`` marker and add explicit attribute type annotations to
``UserStory`` (and the common ``id``/``version``/``created_date``/
``modified_date`` fields on every resource) as a pilot for static type
checker support (mypy, pyright, ty). No runtime behaviour changes - values
are still set dynamically from the API response. A ``typing`` tox/CI job
runs mypy over the package to keep this from regressing; the remaining
resource classes are not yet annotated and will follow incrementally.

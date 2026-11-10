Fixed calling methods of Vue components with `poll=False`, e.g.,
`await widget["ref"].method(poll=False)` which always failed with an
`AssertionError`.

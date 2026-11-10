**Fixed:**

* Fixed calling methods of Vue components with `poll=False`, e.g.,
  `await widget["ref"].method(poll=False)` which always failed with an
  `AssertionError`.
* Fixed reporting of errors when calling methods of Vue components. Errors
  raised in the browser are now reported as an `InvocationError` instead of
  cancelling the call with a `CancelledError`.

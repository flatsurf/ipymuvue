Fixed reporting of errors when calling methods of Vue components. Errors
raised in the browser are now reported as an `InvocationError` instead of
cancelling the call with a `CancelledError`.

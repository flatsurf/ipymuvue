r"""
Referencing subcomponents in Vue templates.
"""
# ******************************************************************************
# Copyright (c) 2022 Julian Rüth <julian.rueth@fsfe.org>
#
# ipymuvue is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ipymuvue is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ipymuvue. If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************


class InvocationError(Exception):
    r"""
    Records a function invocation on the frontend tha failed for the view with
    ``identifier``.
    """

    def __init__(self, message, identifier):
        super().__init__(message)
        self.identifier = identifier


class Subcomponent:
    r"""
    A subcomponent in each view of a :class:`VueWidget`.
    """

    def __init__(self, parent, ref):
        self._parent = parent
        self._ref = ref

    async def views():
        r"""
        Return identifiers of all the views present in the frontend.
        """
        raise NotImplementedError

    def __getattr__(self, name):
        r"""
        Return a handle for the method or property ``name`` of this component.
        """
        return SubcomponentMethod(self, name)

    def __getitem__(self, name):
        r"""
        Return a subcomponent of this subcomponent, the one with
        ``ref="name"``.
        """
        return Subcomponent(self, name)

    @staticmethod
    def _set_result(result, content, *, return_when, views, identify):
        r"""
        Set the result of an invocation into the future ``result``.
        """
        if isinstance(views, str):
            Subcomponent._set_single_result(result, content, identify=identify)
            return

        if return_when == "FIRST_COMPLETED":
            Subcomponent._set_single_result(result, content, identify=identify)
            return

        if return_when == "FIRST_EXCEPTION":
            Subcomponent._set_awaited_results(result, content, identify=identify)
            return

        assert return_when == "ALL_COMPLETED"

        Subcomponent._set_awaitable_results(result, content, identify=identify)

    @staticmethod
    def _set_single_result(result, content, *, identify):
        if len(content) != 1:
            raise ValueError(f"Expected exactly one result but found {results}")

        content = content[0]

        view = content["view"]

        if "error" in content:
            raise InvocationError(content["error"], content["view"])

        value = content.get("result", None)

        result.set_result([value, view] if identify else value)

    @staticmethod
    def _set_awaited_results(result, content, *, identify):
        for c in content:
            if "error" in c:
                raise InvocationError(c["error"], c["view"])

        results = [(c.get("result", None), c["view"]) for c in content]

        result.set_result(results if identify else [r[0] for r in results])

    @staticmethod
    def _set_awaitable_results(result, content, identify):
        if identify:
            raise NotImplementedError("cannot identify views yet")

        def create_awaitable(content):
            view = content["view"]

            import asyncio

            awaitable = asyncio.get_running_loop().create_future()

            if "error" in content:
                awaitable.set_exception(InvocationError(content["error"], view))
            else:
                value = content.get("result")
                awaitable.set_result((value, view) if identify else value)

            return awaitable

        result.set_result([create_awaitable(c) for c in content])

    async def _invoke(self, path, target, args, return_when, identify, views, poll):
        r"""
        Implements :meth:`SubcomponentMethod.__call__`.
        """
        path = [self._ref] + path

        from ipymuvue.widgets import VueWidget

        if not isinstance(self._parent, VueWidget):
            return await self._parent._invoke(
                path=path,
                target=target,
                args=args,
                return_when=return_when,
                identify=identify,
                views=views,
                poll=poll,
            )

        widget = self._parent

        # A random identifier so we can associate answers from the frontend
        # with this invocation.
        import uuid

        identifier = uuid.uuid4().hex

        # A future that signals that the invocation has run to completion in
        # the frontend.
        import asyncio

        result = asyncio.get_running_loop().create_future()

        def on_msg(_, content, __):
            try:
                if content.get("identifier", None) == identifier:
                    assert return_when != "IGNORE"
                    assert "results" in content

                    Subcomponent._set_result(
                        result,
                        content["results"],
                        return_when=return_when,
                        views=views,
                        identify=identify,
                    )

            except Exception:
                result.cancel()
                raise

        with widget._on_msg(on_msg):
            widget.send(
                dict(
                    target=target,
                    path=path,
                    identifier=identifier,
                    args=args,
                    return_when=return_when,
                    views=views,
                )
            )

            if return_when == "IGNORE":
                return

            from ipymuvue.widgets.asynchronous import run

            return await run(result, poll=poll)


class SubcomponentMethod:
    r"""
    A method or property on a subcomponent of a :class:`VueWidget`.
    """

    def __init__(self, subcomponent, method):
        self._subcomponent = subcomponent
        self._method = method

    async def __call__(
        self,
        *args,
        return_when="FIRST_EXCEPTION",
        identify=False,
        views=None,
        poll=True,
    ):
        r"""
        Invoke this method with positional arguments.

        Note that there are no keyword arguments in JavaScript (at least not
        natively) so we can only invoke functions with positional arguments.

        INPUT:

        - ``return_when`` -- when the returned future settles, similar to the standard
          :meth:`asyncio.wait` argument:

          - ``FIRST_COMPLETED`` -- when any call finishes or is cancelled
          - ``FIRST_EXCEPTION`` -- when any call finishes by raising an exception; if
            none raise, equivalent to ``ALL_COMPLETED``
          - ``ALL_COMPLETED`` -- when all calls finished or raised an exception
          - ``IGNORE`` -- do not wait for any methods to return

        - ``identify`` -- whether to return the results with an identifier that
          can be used for ``views``

        - ``views`` -- a single identifier of a view, a list of identifiers,
          or ``None`` (the default); on which target(s) to call the method; if
          ``None``, the method is called on all views.

        - ``poll`` -- whether to use ``jupyter_ui_poll``, to not block the
          Jupyter notebook while the method is running.

        OUTPUT:

        Returns ``None`` if ``return_when`` has been set to ``IGNORE``.

        Returns the value of the call if ``views`` is an identifier or if
        ``return_when`` is ``FIRST_COMPLETED``. If ``identify`` is also set,
        returns a pair ``(value, identifier)``.

        Returns a list of futures otherwise. These futures resolve to a value,
        an exception or a pair ``(value, identifier)`` as above.

        """
        return await self._subcomponent._invoke(
            path=[],
            target=self._method,
            args=args,
            return_when=return_when,
            identify=identify,
            views=views,
            poll=poll,
        )

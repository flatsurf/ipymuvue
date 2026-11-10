Fixed loading components written in Python when several such components
are created in quick succession, e.g., when running all cells of a
notebook. Previously, this sometimes failed with a `ModuleNotFoundError`.

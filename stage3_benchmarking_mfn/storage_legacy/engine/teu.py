"""TEU scaling factor by calculation method.

Faithful port of the VBA (see reference/vba_dump/all_modules.vba)::

    If method = "TEU Simple" Then
        If containerLength < 40 Then teu = 1 Else teu = 2
    ElseIf method = "TEU Advanced" Then
        teu = containerLength / 20

For the "Container" method the workbook multiplies by neither ``teu`` nor 1
explicitly, i.e. revenue is per box -> factor 1.0.
"""
from __future__ import annotations

from .models import METHOD_CONTAINER, METHOD_TEU_ADVANCED, METHOD_TEU_SIMPLE


def teu_factor(container_length: float, method: str) -> float:
    """Return the multiplier applied to a container's storage revenue."""
    if method == METHOD_CONTAINER:
        return 1.0
    if method == METHOD_TEU_SIMPLE:
        return 1.0 if container_length < 40 else 2.0
    if method == METHOD_TEU_ADVANCED:
        return container_length / 20.0
    raise ValueError(f"Unknown calculation method: {method!r}")

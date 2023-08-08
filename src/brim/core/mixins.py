"""Mixin classes providing common properties for models."""
from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from sympy.physics.mechanics import ReferenceFrame, RigidBody, Vector
from sympy.physics.mechanics._system import System

if TYPE_CHECKING:
    with contextlib.suppress(ImportError):
        from brim.utilities.plotting import PlotModel


class NewtonianBodyMixin:
    """Mixin class adding a Newtonian body to a model."""

    def _define_objects(self) -> None:
        """Define the objects of the model."""
        super()._define_objects()
        body = RigidBody(self.name)
        self._system = System.from_newtonian(body)

    @property
    def descriptions(self) -> dict[Any, str]:
        """Descriptions of the symbols used in defining the body."""
        body = self.body
        inertia_matrix = body.central_inertia.to_matrix(body.frame)
        descriptions = {
            body.mass: f"Mass of body: '{body.name}'.",
        }
        for i, axis in enumerate("xyz"):
            for j, axis2 in enumerate("xyz"):
                descriptions[inertia_matrix[i, j]] = (f"Inertia scalar {axis}{axis2} of"
                                                      f" body: '{body.name}'.")
        return {obj: desc for obj, desc in descriptions.items() if obj}  # Drop zeros

    @property
    def body(self) -> RigidBody:
        """The body representing the model."""
        return self.system.bodies[0]

    @property
    def frame(self) -> ReferenceFrame:
        """Reference frame of the model."""
        return self.body.frame

    @property
    def x(self) -> Vector:
        """X-axis of model."""
        return self.frame.x

    @property
    def y(self) -> Vector:
        """Y-axis of model."""
        return self.frame.y

    @property
    def z(self) -> Vector:
        """Z-axis of model."""
        return self.frame.z

    def set_plot_objects(self, plot_object: PlotModel) -> None:
        """Set the symmeplot plot objects."""
        super().set_plot_objects(plot_object)
        plot_object.add_body(self.body)

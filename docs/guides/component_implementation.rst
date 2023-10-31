.. _component_implementation_guide:

=====================================
Guidelines on Implementing Components
=====================================

This document describes the guidelines on implementing components. It assumes
familiarity with the component structure used in BRiM :cite:`stienstra_2023_brim` and
the usage of SymPy mechanics and BRiM, as explained in the first two tutorials
:ref:`tutorials`.

BRiM Components
---------------

.. raw:: html

    <svg class="align-center" viewBox="0 0 114.1879 81.337509" width="550px">
        <use xlink:href="../_static/core_uml.svg#coreUML"></use>
    </svg>

The above figure shows the UML diagram of the core components of BRiM. The three core
components all inherit from :class:`brim.core.base_classes.BrimBase`, as they share a
similar define structure. The three core components are:

- :class:`Models<brim.core.base_classes.ModelBase>` - a system with its own respective
  system boundaries, which can be made up of other models.
- :class:`Connections<brim.core.base_classes.ConnectionBase>` - a utility of models in
  describing the interaction between submodels.
- :class:`Load groups<brim.core.base_classes.LoadGroupBase>` - a collection of forces
  and torques associated with a model or connection.

A large part of what is being shared between these components are the definition steps.
The definition steps are decoupled steps that are used to define the component. The
definition steps are:

0. **Define connections** (only in :class:`models<brim.core.base_classes.ModelBase>`):
   Associate the submodels with the connections, such that the connections know the
   submodels they will operate on.
1. **Define objects**: Create the objects, such as symbols reference frames, without
   defining any relationships between them.
2. **Define kinematics**: Establish relationships between the objects'
   orientations/positions, velocities, and accelerations.
3. **Define loads**: Specifies the forces and torques acting upon the system.
4. **Define constraints**: Computes the holonomic and nonholonomic constraints to which
   the system is subject.

The image below shows a schematic visualization of these steps for a rolling disc.

.. raw:: html

    <svg class="align-center" viewBox="0 0 180.37601 43.00629" width="800px">
        <use xlink:href="../_static/definition_steps.svg#definitionSteps"></use>
    </svg>

Setting Submodels and Connections
---------------------------------

To specify the submodels a model or connection requires, one should specify the class
property ``required_models``. This property should be a tuple of
:class:`brim.core.requirement.ModelRequirement`. Based on these requirements, the
metaclass automatically creates properties for each of the required submodels on
runtime. The following simple class shows how to specify the required submodels. ::

    class MyModel(ModelBase):
        """My model."""

        required_models: tuple[ModelRequirement, ...] = (
            ModelRequirement("ground", GroundBase, "Submodel of the ground."),
            ModelRequirement("other_submodel", OtherSubModel, "Other submodel."),
        )

The property created for ``"ground"`` will be like the following: ::

    def ground(self) -> GroundBase:
        """Submodel of the ground."""
        return self._ground

    @ground.setter
    def ground(self, model: GroundBase) -> None:
        """Submodel of the ground."""
        if not (model is None or isinstance(model, GroundBase)):
            raise TypeError(
                f"Ground should be an instance of an subclass of GroundBase, "
                f"but {model!r} is an instance of {type(model)}."
            )
        self._ground = model

Connections should be specified similarly using the class property
``required_connections``, using :class:`brim.core.requirement.ConnectionRequirement`. ::

    class MyModel(ModelBase):
        """My model."""

        required_connections: tuple[ConnectionRequirement, ...] = (
            ConnectionRequirement("connection", MyConnection, "Connection."),
        )

Implementation Define Steps
---------------------------

To implement the "define" steps in a model, connection, or load group, a leading
underscore is added to the method name. For example, ``_define_<step>``. These methods
solely implement the "define" step for the component itself without traversing the
submodels and load groups. :class:`brim.core.base_classes.BrimBase` contains the
implementation of the "define" methods, including traversal, which should be called
by the user. These methods follow the format ``define_<step>``.

We have established several helping guidelines for each define steps. The subsections
below discuss each of these per define step, and provide general code examples of the
expected implementation.

Define Connections
~~~~~~~~~~~~~~~~~~

- If a connection is used, then the submodels of the connection are defined in the
  ``_define_connections`` method. ::

    def _define_connections(self) -> None:
        """Define the connections between the submodels."""
        super()._define_connections()
        self.connection.submodel = self.submodel


Define Objects
~~~~~~~~~~~~~~

- Each model and connection must instantiate its own
  :class:`sympy.physics.mechanics._system.System` instance and assign it to
  ``self._system``. Load groups automatically inherit the system from their parent.
- Symbols, such as masses and lengths, must be added to the ``self.symbols`` dictionary
  with a string as key and the (dynamic)symbol as value.
- Generalized coordinates must be set/added to the mutable ``self.q`` matrix.
- Generalized speeds must be set/added to the mutable ``self.u`` matrix.
- The name of each symbol, generalized coordinate, and generalized speed must be created
  using :meth:`brim.core.base_classes.BrimBase._add_prefix`. This method puts the name
  of the component in front of the symbol name, such that the symbol name is unique.
- Each symbol, generalized coordinate, and generalized speed must have a description in
  the :meth:`brim.core.base_classes.BrimBase.descriptions` property.
- The define objects step for each connection should be called manually because there
  could be dependencies between the define step of a connection and its parent model,
  since it is utility after all.
- Other component specific objects, such as bodies and reference frames, must be defined
  in this stage, but they should not be oriented or positioned yet. ::

    @property
    def descriptions(self) -> dict[Any, str]:
        """Descriptions of the attributes of the object."""
        return {
            **super().descriptions,
            self.symbols["symbol_name"]: "Description of the symbol.",
            self.q[0]: f"First generalized coordinate of {self.name}.",
            self.q[1]: f"Second generalized coordinate of {self.name}.",
            self.u[0]: f"First generalized speed of {self.name}.",
            self.u[1]: f"Second generalized speed of {self.name}.",
        }

    def _define_objects(self) -> None:
        """Define the objects of the system."""
        super()._define_objects()
        # Create symbols and generalized coordinates and speeds.
        self.symbols["symbol_name"] = symbols(self._add_prefix("symbol"))
        self.q = MutableMatrix([dynamicsymbols(self._add_prefix("q1:3"))])
        self.u = MutableMatrix([dynamicsymbols(self._add_prefix("u1:3"))])
        # Instantiate system.
        self._system = System()
        # Call define objects of connections.
        self.connection.define_objects()  # Without leading underscore!
        # Define other objects such as reference frames and bodies.
        ...

Define Kinematics
~~~~~~~~~~~~~~~~~

- It is generally best to first orient the reference frames in this step, and the
  position the reference frames. Next, one can optimize the definition of the
  velocities. Parent models must do this between their submodels.
- The kinematical differential equations, generalized coordinates, and generalized
  speeds must be added to ``self.system``.
- Possibly one can also use joints for the above.
- Again the define kinematics step of each connection should be called manually.
- Generally, make sure to define the velocity of at least one point in the model's or
  connection's system. ::

    def _define_kinematics(self) -> None:
        """Define the kinematics of the system."""
        super()._define_kinematics()
        # Orient frames.
        self.frame.orient_axis(...)
        # Position points and set their velocities.
        self.point.set_pos(...)
        self.point.set_vel(self.system.frame, ...)
        # Add generalized coordinates, speeds, and kdes to the system.
        self.system.add_coordinates(*self.q)
        self.system.add_speed(*self.u)
        self.system.add_kdes(*(self.q.diff() - self.u))
        # Create and add joints.
        self.system.add_joints(...)
        # Call define kinematics of connections.
        self.connection.define_kinematics()  # Without leading underscore!

Define Loads
~~~~~~~~~~~~

- As all points and reference frames have already been defined and positioned, this step
  only requires computation of the forces and torques and adding the to the
  ``self.system``.
- In case non-contributing should be computed, one ought to define and use the auxiliary
  speeds already in the define objects and define kinematics step.
- Again the define loads step of each connection should be called manually. ::

    def _define_loads(self) -> None:
        """Define the loads of the system."""
        super()._define_loads()
        # Add forces, torques and actuators
        self.system.add_loads(
            Force(self.point, ...),
            Torque(self.frame, ...),
            ...
        )
        self.system.add_actuators(...)
        # Call define loads of connections.
        self.connection.define_loads()  # Without leading underscore!

Define Constraints
~~~~~~~~~~~~~~~~~~

- For holonomic constraints a loop is being closed most of the time using a dot product.
  Just make sure to have some method to prevent the creation of constraint which are
  already satisfied. Optionally, you can use
  :class:`brim.utilities.utilities.check_zero`.
- For nonholonomic constraints the major difficulty is in the fact that one cannot
  assume anything about the already defined velocities. Especially points are
  susceptible to have multiple possible velocity definitions. Therefore, it is advised
  to compute the velocity based on the position graph of the points and the orientation
  and angular velocity graph of the reference frames. A good example of this is in the
  :class:`brim.bicycle.tires.NonHolonomicTire` class.  ::

    def _define_constraints(self) -> None:
        """Define the constraints of the system."""
        super()._define_constraints()
        self.add_holonomic_constraints(...)
        self.add_nonholonomic_constraints(...)
        # Call define constraints of connections.
        self.connection.define_constraints()  # Without leading underscore!

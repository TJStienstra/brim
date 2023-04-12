from __future__ import annotations

import pytest
from brim.core import ModelBase, ModelRequirement
from brim.utilities.templates import MyModel, MySubModel
from sympy.physics.mechanics.system import System


class TestModelBase:
    """Test the ModelBase class.

    Explanation
    -----------
    As ModelBase is an abstract class, this test actually uses the templates to test
    certain characteristics of the ModelBase class.
    """

    @pytest.fixture()
    def _create_model(self) -> None:
        self.model = MyModel("model")
        self.model.submodel1 = MySubModel("submodel1")
        self.model.submodel2 = MySubModel("submodel2")
        self.model.define_objects()

    def test_init(self) -> None:
        bike = MyModel("model")
        assert isinstance(bike, ModelBase)
        assert bike.name == "model"
        assert bike.submodel1 is None
        assert bike.submodel2 is None

    @pytest.mark.parametrize("name", ["", " ", "my model", "my,model", "my:model"])
    def test_invalid_name(self, name) -> None:
        with pytest.raises(ValueError):
            MyModel(name)

    @pytest.mark.parametrize("meth", ["define_kinematics", "define_loads"])
    def test_call_traversal(self, _create_model, meth) -> None:
        # Test should ideally also test for the correct order
        def register_call(meth):
            def wrapper():
                call_order.append(meth.__self__.name)
                return meth()

            return wrapper

        call_order = []
        for m in [self.model, self.model.submodel1, self.model.submodel2]:
            setattr(m, meth, register_call(getattr(m, meth)))
        getattr(self.model, meth)()
        assert set(call_order) == {"model", "submodel1", "submodel2"}
        assert len(set(call_order)) == len(call_order)

    def test_get_description_own_description(self, _create_model) -> None:
        assert (self.model.get_description(self.model.q[0]) ==
                self.model.descriptions[self.model.q[0]])

    def test_get_description_of_submodel(self, _create_model) -> None:
        assert self.model.get_description(self.model.submodel1.my_symbol) is not None

    def test_get_description_of_not_existing_symbol(self, _create_model) -> None:
        assert self.model.get_description("not existing symbol") is None

    def test_call_system(self, _create_model) -> None:
        self.model.define_kinematics()
        self.model.define_loads()
        assert isinstance(self.model.system, System)

    def test_add_mixin_simple(self, _create_model) -> None:
        class MyMixin:
            @property
            def my_method(self):
                return 5

        self.model.add_mixin(MyMixin)
        assert isinstance(self.model, MyMixin)
        assert self.model.my_method == 5
        assert isinstance(self.model, MyModel)
        assert isinstance(self.model.submodel1, MySubModel)

    def test_add_mixin_complex(self, _create_model) -> None:
        class MyMixin:
            required_models = (
                ModelRequirement("submodel2", MySubModel, "overwritten"),
                ModelRequirement("submodel3", MySubModel, "desc"),
            )

            @property
            def my_method(self):
                return 5

            def define_objects(self):
                self.new_symbol = 5

        self.model.add_mixin(MyMixin)
        assert isinstance(self.model, MyMixin)
        assert self.model.my_method == 5
        assert isinstance(self.model, MyModel)
        assert isinstance(self.model.submodel1, MySubModel)
        assert self.model.submodel3 is None
        assert self.model.new_symbol == 5
        assert [req.attribute_name for req in self.model.required_models] == [
            "submodel2", "submodel3", "submodel1"]
        # A mixin is not able to overwrite a requirement of the base class, as inherited
        # required_models are overwritten.
        assert self.model.required_models[0].description != "overwritten"

    def test_add_invalid_mixin(self, _create_model) -> None:
        with pytest.raises(TypeError):
            self.model.add_mixin(MyModel("invalid"))

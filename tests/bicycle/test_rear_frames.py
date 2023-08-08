import pytest
from brim.bicycle.rear_frames import RigidRearFrame, RigidRearFrameMoore
from sympy import symbols
from sympy.physics.mechanics import Point

try:
    from brim.utilities.plotting import PlotModel
    from symmeplot import PlotBody, PlotLine
except ImportError:
    PlotModel = None


class TestRigidRearFrame:
    def test_default(self) -> None:
        front = RigidRearFrame("rear")
        assert isinstance(front, RigidRearFrameMoore)

    @pytest.mark.parametrize("formulation_name, expected_class", [
        ("moore", RigidRearFrameMoore),
    ])
    def test_init(self, formulation_name, expected_class) -> None:
        front = RigidRearFrame.from_formulation(formulation_name, "rear")
        assert isinstance(front, expected_class)

    def test_init_error(self) -> None:
        with pytest.raises(ValueError):
            RigidRearFrame.from_formulation("not_implemented", "rear")


class TestRigidRearFrameMoore:
    def test_default(self):
        rear = RigidRearFrameMoore("rear")
        rear.define_objects()
        assert rear.name == "rear"
        assert rear.frame == rear.body.frame
        assert isinstance(rear.steer_attachment, Point)
        assert isinstance(rear.wheel_attachment, Point)
        assert isinstance(rear.saddle, Point)
        assert rear.wheel_axis == rear.y

    def test_kinematics(self):
        rear = RigidRearFrameMoore("rear")
        rear.define_objects()
        rear.define_kinematics()
        # Test if kinematics is defined
        rear.steer_attachment.pos_from(rear.body.masscenter)
        rear.wheel_attachment.pos_from(rear.body.masscenter)
        rear.saddle.pos_from(rear.body.masscenter)
        # Test velocities
        assert rear.body.masscenter.vel(rear.frame) == 0
        assert rear.steer_attachment.vel(rear.frame) == 0
        assert rear.wheel_attachment.vel(rear.frame) == 0
        assert rear.saddle.vel(rear.frame) == 0

    def test_descriptions(self):
        rear = RigidRearFrameMoore("rear")
        rear.define_objects()
        for length in rear.symbols.values():
            assert rear.descriptions[length] is not None

    @pytest.mark.skipif(PlotModel is None, reason="symmeplot not installed")
    @pytest.mark.parametrize("pedals_center_point", [None, Point("P")])
    def test_set_plot_objects(self, pedals_center_point):
        lx, lz = symbols("lx lz")
        rear = RigidRearFrameMoore("rear")
        rear.define_all()
        if pedals_center_point is not None:
            pedals_center_point.set_pos(rear.wheel_attachment,
                                        lx * rear.x + lz * rear.z)
        plot_model = PlotModel(rear.system.frame, rear.system.origin, rear)
        assert len(plot_model.children) == 2
        assert any(isinstance(obj, PlotBody) for obj in plot_model.children)
        assert any(isinstance(obj, PlotLine) for obj in plot_model.children)

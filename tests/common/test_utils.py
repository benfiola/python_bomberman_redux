import pytest
import python_bomberman.common.utils as utils


class TestSuite:
    @pytest.fixture
    def coordinate(self):
        return utils.Coordinate(3, 5)

    def test_init(self, coordinate):
        assert len(coordinate) == 2

    def test_x(self, coordinate):
        assert coordinate.x == 3

    def test_y(self, coordinate):
        assert coordinate.y == 5

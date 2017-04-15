import python_bomberman as module_under_test
import pytest
import os

dir = os.path.dirname(module_under_test.__file__)
pytest.main([dir])
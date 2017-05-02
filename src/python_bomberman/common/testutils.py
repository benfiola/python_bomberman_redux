import pytest
import random
import string
import os


@pytest.fixture
def temp_file(tmpdir):
    filename = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    return os.path.join(str(tmpdir), filename)

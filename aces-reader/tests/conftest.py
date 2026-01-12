import os.path

import pytest


@pytest.fixture
def fixtures():
    fixtures_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        'fixtures'
    ))

    yield fixtures_dir

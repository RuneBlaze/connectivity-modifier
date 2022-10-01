import pytest
from hm01.context import context as _context
@pytest.fixture
def context():
    return _context.with_working_dir("tests/hm01_working_dir").as_transient()
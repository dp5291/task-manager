import copy

import pytest

from services.tasks import TASKS


@pytest.fixture(autouse=True)
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(snapshot)

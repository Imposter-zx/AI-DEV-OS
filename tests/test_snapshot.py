import json
from pathlib import Path

import pytest

from ai_dev_os.utils.snapshot import SnapshotManager


@pytest.fixture
def snapshot_manager(tmp_path):
    return SnapshotManager(base_dir=tmp_path)


def test_save_snapshot_creates_file(snapshot_manager):
    state_dict = {"id": "123", "phase": "brainstorming", "data": "test"}

    path = snapshot_manager.save_snapshot("123", "brainstorming", state_dict)

    assert path.exists()
    assert "wf_123_brainstorming_" in path.name
    with open(path, "r") as f:
        data = json.load(f)
        assert data == state_dict


def test_load_latest_snapshot(snapshot_manager):
    workflow_id = "456"
    state1 = {"id": workflow_id, "phase": "brainstorming"}
    state2 = {"id": workflow_id, "phase": "planning"}

    snapshot_manager.save_snapshot(workflow_id, "brainstorming", state1)
    import time

    time.sleep(1.1)  # Ensure different timestamp
    snapshot_manager.save_snapshot(workflow_id, "planning", state2)

    latest = snapshot_manager.load_latest_snapshot(workflow_id)

    assert latest["phase"] == "planning"


def test_load_non_existent_snapshot(snapshot_manager):
    assert snapshot_manager.load_latest_snapshot("non-existent") is None


def test_list_snapshots(snapshot_manager):
    workflow_id = "789"
    snapshot_manager.save_snapshot(workflow_id, "p1", {})
    snapshot_manager.save_snapshot(workflow_id, "p2", {})

    snapshots = snapshot_manager.list_snapshots(workflow_id)
    assert len(snapshots) == 2

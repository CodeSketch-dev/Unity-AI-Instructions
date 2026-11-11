from app.automation.meshy_export import pick_new_task


def task(tid, status, tris=1000, url="u"):
    return {"id": tid, "status": status, "triangleCount": tris, "result": {"texture": {"modelUrl": url}}}


def test_new_task_still_running_is_waited_for_not_skipped():
    tasks = [task("new", "IN_PROGRESS"), task("old", "SUCCEEDED")]
    picked, state = pick_new_task(tasks, exclude={"old"})
    assert picked is None and state == "waiting"   # the old finished task must never be exported


def test_new_finished_task_is_picked():
    tasks = [task("new", "SUCCEEDED"), task("old", "SUCCEEDED")]
    picked, state = pick_new_task(tasks, exclude={"old"})
    assert picked["id"] == "new" and state == "ready"


def test_no_new_task_yet():
    picked, state = pick_new_task([task("old", "SUCCEEDED")], exclude={"old"})
    assert picked is None and state == "waiting"


def test_new_task_failed():
    picked, state = pick_new_task([task("new", "FAILED"), task("old", "SUCCEEDED")], exclude={"old"})
    assert picked is None and state == "failed"


def test_without_exclude_keeps_old_behaviour():
    picked, state = pick_new_task([task("a", "IN_PROGRESS"), task("b", "SUCCEEDED")], exclude=None)
    assert picked["id"] == "b" and state == "ready"

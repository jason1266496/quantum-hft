"""Pure update-ID classification, independent of book contents or event time."""

from .types import BookError


def classify_update(snapshot_update_id, local_update_id, applied_event_count,
                    first_update_id, final_update_id):
    """Return (classification, action); a STOP must terminate the owning book."""
    values = (snapshot_update_id, local_update_id, applied_event_count,
              first_update_id, final_update_id)
    if any(type(value) is not int or value < 0 for value in values):
        raise BookError("INVALID_UPDATE_ID", "IDs and applied count must be nonnegative integers")
    if first_update_id > final_update_id:
        raise BookError("INVALID_UPDATE_ID", "first update ID exceeds final update ID")
    if local_update_id < snapshot_update_id or (
        applied_event_count == 0 and local_update_id != snapshot_update_id
    ):
        raise BookError("INVALID_CONTINUITY_STATE", "local update ID disagrees with snapshot progress")
    if applied_event_count == 0:
        if final_update_id <= snapshot_update_id:
            return "STALE_BEFORE_SNAPSHOT", "SKIP"
        if not first_update_id <= snapshot_update_id + 1 <= final_update_id:
            return "FIRST_EVENT_BRIDGE_FAILURE", "STOP"
    else:
        if final_update_id <= local_update_id:
            return "STALE_OR_DUPLICATE", "SKIP"
        if first_update_id > local_update_id + 1:
            return "UPDATE_ID_GAP", "STOP"
    if first_update_id == local_update_id + 1:
        return "CONTIGUOUS", "APPLY"
    return "OVERLAPPING_CONTIGUOUS", "APPLY"

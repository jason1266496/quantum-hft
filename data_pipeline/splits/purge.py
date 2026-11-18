"""Purge using the actual future label endpoint, including equality at boundary."""
def crosses_boundary(current_time,target_time,boundary):
    return (boundary is not None and target_time is not None
            and current_time<boundary<=target_time)

def purge_reason(current_time,target_time,boundary):
    return "PURGED_LABEL_WINDOW_CROSSES_SPLIT" if crosses_boundary(current_time,target_time,boundary) else ""

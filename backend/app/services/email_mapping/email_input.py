"""Prepare the school file and invalidate stale email results."""
import hashlib


# Fingerprint the current school file and selected worksheet for email mapping.
def email_input_signature(state):
    source = state.get("saved_admission_school")
    if not source:
        return None
    sheet = state.get("admission_settings", {}).get("admission_school_sheet")
    return hashlib.sha256(source["data"] + repr(sheet).encode()).hexdigest()


# Invalidate saved Email and downstream Class data when direct inputs change.
def sync_email_stage(state):
    from app.api.file_workflow_invalidation import clear_class_mapping
    signature = email_input_signature(state)
    ready = bool(signature)
    state.pop("email_handoff_signature", None)
    result_signature = state.get("email_result_signature") or ()
    values = state.get("admission_settings", {})
    school_index = (state.get("saved_admission_dump", {}).get("school_index")
                    or values.get("workspace_school_index"))
    current_result = (
        len(result_signature) == 6
        and result_signature[4] == "email_first_name_school_v13"
        and result_signature[5] == school_index
    )
    legacy_result = (
        len(result_signature) == 5
        and result_signature[3] == "email_first_name_school_v12"
        and result_signature[4] == school_index
    )
    school_changed = bool(state.get("email_exports")) and not (current_result or legacy_result)
    if state.get("email_source_signature") != signature or school_changed:
        state.pop("saved_email_dump", None)
        state.pop("email_exports", None)
        state.pop("email_result_signature", None)
        clear_class_mapping(state)
    state["email_source_signature"] = signature
    return ready

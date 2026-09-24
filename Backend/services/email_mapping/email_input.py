"""Prepare admission misses and invalidate stale email results."""
import hashlib


def email_school_input(rows):
    """Keep school fields and discard admission-mapping audit columns at handoff."""
    return rows.drop(columns=[column for column in rows.columns
                              if str(column).startswith("mapping_")])


# Fingerprint the current admission misses and name settings for email mapping.
def email_input_signature(state):
    exports = state.get("admission_exports", {})
    source = exports.get("not_matched.xlsx")
    ready = bool(source and source["count"])
    signature = None
    if ready:
        settings = state.get("admission_settings", {})
        # Use the column that produced the saved admission results, not a draft selection.
        admission_signature = state.get("admission_signature") or ()
        name_column = admission_signature[6] if len(admission_signature) > 6 else settings.get("school_name_col")
        signature = hashlib.sha256(source["data"] +
            repr((name_column, settings.get("admission_name_mode"))).encode()).hexdigest()
    return signature


# Invalidate saved email data when the current Not matched students change.
def sync_email_stage(state):
    signature = email_input_signature(state)
    ready = bool(signature)
    state.pop("email_handoff_signature", None)
    result_signature = state.get("email_result_signature") or ()
    school_changed = bool(state.get("email_exports")) and (
        len(result_signature) != 5 or result_signature[3] != "email_first_name_school_v12"
        or result_signature[4] != state.get("saved_admission_dump", {}).get("school_index"))
    if state.get("email_source_signature") != signature or school_changed:
        state.pop("saved_email_dump", None)
        state.pop("email_exports", None)
        state.pop("email_result_signature", None)
        state.pop("full_name_class_exports", None)
        state.pop("full_name_class_round_one_exports", None)
        state.pop("full_name_class_result_signature", None)
    state["email_source_signature"] = signature
    return ready




def email_pass_one_complete(state):
    """Require successful pass-one artifacts for the current source and settings."""
    values = state.get('admission_settings', {})
    source = email_input_signature(state)
    signature = (source, values.get('email_input_column'), values.get('email_first_name_column'),
                 'email_first_name_school_v12', state.get('saved_admission_dump', {}).get('school_index'))
    exports = state.get('email_exports', {})
    return bool(source and state.get('saved_email_dump')
                and all(name in exports for name in ('email_matched.xlsx', 'email_review.xlsx', 'email_not_matched.xlsx'))
                and tuple(state.get('email_result_signature') or ()) == signature)

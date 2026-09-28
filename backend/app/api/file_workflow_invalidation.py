"""Clear mapping artifacts when an input or upstream mapping changes."""


def clear_class_mapping(state):
    state.pop('full_name_class_exports', None)
    state.pop('full_name_class_result_signature', None)


def clear_email_and_class_mapping(state):
    state.pop('saved_email_dump', None)
    state.pop('email_exports', None)
    state.pop('email_result_signature', None)
    state.pop('email_source_signature', None)
    clear_class_mapping(state)


def clear_all_mappings(state):
    state.pop('admission_exports', None)
    state.pop('admission_signature', None)
    clear_email_and_class_mapping(state)


# Purpose: Removes saved results that become stale when upstream inputs change.
# clear_class_mapping removes only full-name/class exports and their committed signature.
# clear_email_and_class_mapping also removes email dumps, exports, and email signatures.
# clear_all_mappings additionally removes admission exports and the admission signature.
# The layered functions encode the dependency order between the three mapping stages.
# Used by: file-input routes invalidate downstream artifacts after file changes or clears.
# Admission mapping clears email/class results when it commits new admission results.
# Email mapping and email-input synchronization clear class results when inputs change.

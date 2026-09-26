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

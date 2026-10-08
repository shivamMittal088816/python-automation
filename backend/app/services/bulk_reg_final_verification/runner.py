"""Orchestrate every final bulk-registration verification stage."""
import pandas as pd

from .account_fields import field_stages
from .database import database_stage
from .email_format import email_format_stage
from .sanity import final_sanity_stages
from .username_match import first_name_stage
from .common import row_stage


def verify_final_output(frame, existing_usernames=(), existing_emails=(), house_ids=()):
    username_stages = field_stages(frame, 'user_name', 'username')
    email_stages = field_stages(frame, 'EMAIL', 'email')
    stages = [
        username_stages[0],
        email_stages[0],
        username_stages[1],
        email_stages[1],
        email_format_stage(frame),
        database_stage(frame, 'user_name', 'username', existing_usernames),
        database_stage(frame, 'EMAIL', 'email', existing_emails),
        first_name_stage(frame),
        *final_sanity_stages(frame),
    ]
    if 'house' in frame:
        houses = frame['house'].fillna('').astype(str).str.strip()
        known = {str(value).strip() for value in house_ids if value is not None}
        unresolved = set(frame.attrs.get('unresolved_house_positions', []))
        invalid = [bool(value) and (value not in known or position in unresolved)
                   for position, value in enumerate(houses)]
        stages.append(row_stage(
            frame, 'house_index', 'Every supplied house resolves to a database index',
            pd.Series(invalid, index=frame.index, dtype=bool),
        ))
    return {
        'passed': all(stage['passed'] for stage in stages),
        'checked_records': len(frame),
        'stages': stages,
    }

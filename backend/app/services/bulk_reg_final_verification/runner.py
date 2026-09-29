"""Orchestrate every final bulk-registration verification stage."""

from .account_fields import field_stages
from .database import database_stage
from .email_format import email_format_stage
from .sanity import final_sanity_stages
from .username_match import first_name_stage


def verify_final_output(frame, existing_usernames=(), existing_emails=()):
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
    return {
        'passed': all(stage['passed'] for stage in stages),
        'checked_records': len(frame),
        'stages': stages,
    }

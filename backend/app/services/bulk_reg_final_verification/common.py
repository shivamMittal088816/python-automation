"""Shared result builders for final bulk-registration verification stages."""


def failed_records(frame, mask):
    positions = [position for position, failed in enumerate(mask) if failed]
    return {
        'columns': ['Preview row', *frame.columns.tolist()],
        'rows': [
            [position + 1, *frame.iloc[position].fillna('').tolist()]
            for position in positions
        ],
        'row_count': len(positions),
    }


def row_stage(frame, stage_id, title, mask):
    return {
        'id': stage_id,
        'title': title,
        'passed': not mask.any(),
        'issues': [position + 1 for position, failed in enumerate(mask) if failed],
        'failed_records': failed_records(frame, mask),
    }

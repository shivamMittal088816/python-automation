SELECT DISTINCT
    u.user_id,
    CONCAT_WS(' ', u.user_firstname, u.user_lastname) AS fullname,
    pu.admission_number,
    u.user_name,
    u.user_edu_class,
    u.user_edu_major,
    u.user_firstname,
    u.user_lastname,
    u.user_package,
    u.user_email,
    LOWER(
        REPLACE(
            CONCAT_WS(
                ' ',
                u.user_firstname,
                NULLIF(u.user_lastname, ''),
                CASE
                    WHEN u.user_package = 14 THEN u.user_edu_class
                    WHEN u.user_package = 12 THEN u.user_edu_class + 1
                    WHEN u.user_package = 11 THEN u.user_edu_class + 2
                    ELSE u.user_edu_class
                END
            ),
            ' ',
            ''
        )
    ) AS generated_col
FROM users u
JOIN paid_users pu ON u.user_id = pu.user_id
WHERE u.user_edu_school = :school_index
  AND u.user_type = '0'

SELECT DISTINCT
    u.user_id,
    u.user_name,
    u.user_edu_class,
    u.user_edu_major,
    u.user_firstname,
    u.user_lastname,
    u.user_package,
    u.user_email,
    u.user_edu_school
FROM users u
WHERE LOWER(u.user_email) IN :emails

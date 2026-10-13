SELECT
    user_id,
    user_firstname,
    user_lastname,
    user_email,
    user_edu_class,
    user_package
FROM users
WHERE (:cursor IS NULL OR user_id > :cursor)
ORDER BY user_id ASC
LIMIT :limit

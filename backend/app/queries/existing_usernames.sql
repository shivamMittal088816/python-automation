SELECT u.user_name
FROM users AS u
WHERE LOWER(TRIM(u.user_name)) IN :usernames

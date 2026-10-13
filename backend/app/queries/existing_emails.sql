SELECT u.user_email
FROM users AS u
WHERE LOWER(TRIM(u.user_email)) IN :emails

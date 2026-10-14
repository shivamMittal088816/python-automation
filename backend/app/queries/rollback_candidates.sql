SELECT u.user_id,
       u.user_edu_class,
       u.user_package,
       u.user_activated,
       u.user_subscribed,
       u.user_subscription_date
FROM users AS u
WHERE u.user_edu_school = :school_index
  AND u.user_type = '0'
  AND u.user_package = 14
ORDER BY u.user_id

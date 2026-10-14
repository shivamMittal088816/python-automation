UPDATE users
SET user_package = 12,
    user_subscribed = '0',
    user_activated = '0',
    user_edu_class = CAST(TRIM(user_edu_class) AS UNSIGNED) - 1,
    user_subscription_date = '2025-04-01 00:00:00'
WHERE user_edu_school = :school_index
  AND user_type = '0'
  AND user_package = 14
  AND user_id NOT IN :supplied_ids

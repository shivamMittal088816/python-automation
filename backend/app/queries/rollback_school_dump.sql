SELECT DISTINCT
    u.user_id,
    pu.admission_number,
    u.user_name,
    u.user_edu_class,
    u.user_edu_major,
    u.user_firstname,
    u.user_lastname,
    CONCAT_WS(' ', u.user_firstname, u.user_lastname) AS fullname,
    u.user_email,
    u.user_edu_school,
    u.user_package,
    u.user_activated,
    u.user_subscribed,
    u.user_subscription_date
FROM users u
JOIN paid_users pu ON u.user_id = pu.user_id
WHERE u.user_edu_school = :school_index
  AND u.user_type = '0'
  AND u.user_package = '14'

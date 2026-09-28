"""Allocate and verify bulk-registration usernames against MySQL."""
from sqlalchemy import bindparam, text


def fetch_available_usernames(first_names):
    prefixes = [str(name).strip().lower() for name in first_names if str(name).strip()]
    if not prefixes:
        return []

    prefix_rows = ['SELECT :prefix_0 AS prefix']
    prefix_rows.extend(
        f'UNION ALL SELECT :prefix_{index}' for index in range(1, len(prefixes))
    )
    query = text(f'''WITH
digits AS (
    SELECT 0 AS d
    UNION ALL SELECT 1
    UNION ALL SELECT 2
    UNION ALL SELECT 3
    UNION ALL SELECT 4
    UNION ALL SELECT 5
    UNION ALL SELECT 6
    UNION ALL SELECT 7
    UNION ALL SELECT 8
    UNION ALL SELECT 9
),
numbers AS (
    SELECT (a.d * 1000) + (b.d * 100) + (c.d * 10) + d.d AS n
    FROM digits a
    CROSS JOIN digits b
    CROSS JOIN digits c
    CROSS JOIN digits d
    WHERE (a.d * 1000) + (b.d * 100) + (c.d * 10) + d.d BETWEEN 1 AND 1999
),
prefixes AS (
    {' '.join(prefix_rows)}
),
ranked_prefixes AS (
    SELECT prefix, ROW_NUMBER() OVER (PARTITION BY prefix ORDER BY prefix) AS rn
    FROM prefixes
),
available_numbers AS (
    SELECT p.prefix, n.n,
           ROW_NUMBER() OVER (PARTITION BY p.prefix ORDER BY n.n) AS rn
    FROM (SELECT DISTINCT prefix FROM prefixes) p
    CROSS JOIN numbers n
    LEFT JOIN users u
      ON u.user_name = CASE
          WHEN n.n < 1000 THEN CONCAT(p.prefix, LPAD(n.n, 3, '0'))
          ELSE CONCAT(p.prefix, n.n)
      END
    WHERE u.user_name IS NULL
)
SELECT CASE
           WHEN an.n < 1000 THEN CONCAT(rp.prefix, LPAD(an.n, 3, '0'))
           ELSE CONCAT(rp.prefix, an.n)
       END AS available_username
FROM ranked_prefixes rp
JOIN available_numbers an
  ON rp.prefix = an.prefix
 AND rp.rn = an.rn
ORDER BY rp.prefix, an.n''')
    parameters = {f'prefix_{index}': prefix for index, prefix in enumerate(prefixes)}
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(query, parameters).all()
    return [str(row[0]) for row in rows]


def fetch_existing_usernames(usernames):
    values = sorted({str(username).strip() for username in usernames if str(username).strip()})
    if not values:
        return set()
    query = text('''SELECT u.user_name
FROM users AS u
WHERE u.user_name IN :usernames''').bindparams(bindparam('usernames', expanding=True))
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(query, {'usernames': values}).all()
    return {str(row[0]) for row in rows}

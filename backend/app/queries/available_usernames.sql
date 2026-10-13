WITH RECURSIVE
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
prefix_indexes AS (
    SELECT 0 AS position
    UNION ALL
    SELECT position + 1
    FROM prefix_indexes
    WHERE position + 1 < JSON_LENGTH(:prefixes_json)
),
prefixes AS (
    SELECT JSON_UNQUOTE(
        JSON_EXTRACT(:prefixes_json, CONCAT('$[', position, ']'))
    ) AS prefix
    FROM prefix_indexes
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
ORDER BY rp.prefix, an.n

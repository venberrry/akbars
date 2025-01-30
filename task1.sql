-- 1.1

SELECT
    c.id_client,
    c.location,
    SUM(EXTRACT(EPOCH FROM (call.dt_end - call.dt_start)) / 60) AS total_call_duration_minutes
FROM calls AS call
JOIN
    clients AS c ON call.id_client = c.id_client
WHERE c.location = 'Moscow'
GROUP BY c.id_client, c.location;

-- 1.2

SELECT
    c.id_client,
    c.location,
    c.dt_birth,
    CURRENT_DATE - c.dt_birth AS age
FROM clients AS c
WHERE CURRENT_DATE - c.dt_birth < INTERVAL '30 years';

-- 1.3

SELECT
    c.id_client,
    cr.client_reaction
FROM client_reactions AS cr
JOIN
    calls AS call ON cr.id_call = call.id_call
JOIN
    clients AS c ON call.id_client = c.id_client
WHERE
    cr.client_reaction IN ('bad', 'normal');



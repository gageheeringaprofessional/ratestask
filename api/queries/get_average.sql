-- Average price between origin and destination in date range
-- for each day where at least 3 transactions took place
SELECT txs.day,
	CASE WHEN day_counts.day_count >= 3 THEN AVG(txs.price)
		ELSE null
	END AS average
FROM (
	-- Transactions within relevant regions and date range
	SELECT day, price
	FROM prices
	WHERE orig_code {orig_in_or_equals} %(origin)s -- API replaces {orig_in_or_equals} with IN or =
	AND dest_code {dest_in_or_equals} %(destination)s -- API replaces {orig_in_or_equals} with IN or =
	AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
) txs
LEFT JOIN (
	-- Transaction count for each day within relevant regions and date range
	SELECT t.day, COUNT(*) as day_count
	FROM (
		-- Transactions within relevant regions and date range
		SELECT day, id
		FROM prices
		WHERE orig_code {orig_in_or_equals} %(origin)s -- API replaces {orig_in_or_equals} with IN or =
		AND dest_code {dest_in_or_equals} %(destination)s -- API replaces {orig_in_or_equals} with IN or =
		AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
		GROUP BY day, id
	) t
	GROUP BY day
) day_counts
ON txs.day = day_counts.day
GROUP BY txs.day, day_counts.day_count
ORDER BY txs.day ASC
;
SELECT AVG(price)
FROM prices
WHERE orig_code = %(orig_code)s
AND dest_code = %(dest_code)s
AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
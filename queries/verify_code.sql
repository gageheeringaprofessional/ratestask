-- verify a code exists
SELECT EXISTS(
	SELECT 1
	FROM ports
	WHERE code = %(target)s
)
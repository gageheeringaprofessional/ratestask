from setuptools import setup

setup(
	name='api'
	, version='1.0'
	, description='ratestask API for Xeneta'
	, author='Gage Heeringa'
	, author_email='gageheeringa@protonmail.com'
	, install_requires=['Flask', 'Psycopg2', 'pytest']
)
from setuptools import setup, find_packages

setup(
    name='cvid',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['cvid=cvid.main:main'],
    }
)

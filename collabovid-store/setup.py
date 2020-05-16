from setuptools import setup, find_packages

setup(
    name='collabovid_store',
    version='1.0',
    packages=find_packages(),
    install_requires=['boto3==1.13.10']
)

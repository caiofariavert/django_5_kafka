#!/usr/bin/env python
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 12):
    raise Exception("Only Python 3.12+ is supported")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="django_kafka",
    version="2.1.1",
    author="VertCapital",
    author_email="thiago@vert-capital.com.br",
    description="Producer and Consumer for Kafka and django projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vert-capital/django-kafka",
    packages=find_packages(exclude=["ez_setup", "examples", "tests", "release"]),
    install_requires=[
        "Django>=5.2",
        "confluent-kafka==2.11.0",
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

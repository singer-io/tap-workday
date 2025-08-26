from setuptools import setup, find_packages


setup(
    name="tap-workday",
    version="0.0.1",
    description="Singer.io tap for extracting data from workday API",
    author="Stitch",
    url="http://singer.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_workday"],
    install_requires=[
        "singer-python==6.1.1",
        "requests==2.32.5",
        "zeep==4.3.1",
        "parameterized==0.9.0",
    ],
    entry_points="""
          [console_scripts]
          tap-workday=tap_workday:main
      """,
    packages=find_packages(),
    package_data={
        "tap_workday": ["schemas/*.json"],
    },
    include_package_data=True,
)

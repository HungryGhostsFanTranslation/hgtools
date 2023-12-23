from setuptools import setup, find_packages

setup(
    name='hgtools',
    version='1.0.0',
    packages=find_packages(),
    py_modules=['hgtools'],
    install_requires=[
        'Click',
        "kaitaistruct",
        'pyyaml',
        'defusedxml'
    ],
    entry_points={
        'console_scripts': [
            'hgtools = hgtools.main:cli',
        ],
    },
)

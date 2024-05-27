from setuptools import setup, find_packages

setup(
    name='hgtools',
    version='1.1.3',
    packages=find_packages(),
    py_modules=['hgtools'],
    install_requires=[
        'Click',
        "kaitaistruct",
        'pyyaml',
        'defusedxml',
        'pypng'
    ],
    entry_points={
        'console_scripts': [
            'hgtools = hgtools.main:cli',
        ],
    },
    include_package_data=True
)

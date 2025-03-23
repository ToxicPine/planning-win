from setuptools import setup, find_packages

setup(
    name="compute-node-cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'splitup-node=cli.commands:cli',
        ],
    },
)
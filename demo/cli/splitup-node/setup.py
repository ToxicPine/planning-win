from setuptools import setup, find_packages

setup(
    name="compute-node-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2.10.6",
        "pydantic-settings>=2.0.0",
        "click",
        "python-dotenv",
        "fastapi>=0.115.11",
        "starlette>=0.46.1",
        "anyio>=4.9.0",
        "typing-extensions>=4.12.2"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "splitup-node=cli.commands:cli",
        ],
    },
)
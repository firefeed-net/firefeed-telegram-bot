from setuptools import setup, find_packages

setup(
    name="firefeed-telegram-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.7",
        "aiolimiter>=1.1.0",
        "aiocache>=0.12.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
        "firefeed-core>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
)
from setuptools import setup, find_packages

setup(
    name="telegram-bot-fastapi",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "aiogram==3.10.0",
        "uvicorn[standard]==0.24.0",
        "python-dotenv==1.0.0",
        "pydantic-settings==2.1.0",
        "aiofiles==23.2.1",
        "python-multipart==0.0.6",
    ],
    extras_require={
        "dev": [
            "ruff==0.1.6",
            "mypy==1.8.0",
            "types-aiofiles==23.2.0.0",
            "types-requests==2.31.0.10",
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
        ],
    },
    python_requires=">=3.11",
)
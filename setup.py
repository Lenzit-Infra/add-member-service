from setuptools import setup, find_packages

setup(
    name="lenzit",  # <--- نام پکیج شما در PyPI
    version="0.1.0",  # یادتان باشد برای هر آپدیت جدید، این عدد را زیاد کنید (مثلا 0.1.1)
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "telethon",
        # سایر وابستگی‌ها
    ],
    author="Mohammad Web",
    author_email="mohmmadweb@gmail.com",
    description="Lenzit Telegram Automation Dashboard",
)
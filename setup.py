# setup.py
from setuptools import setup, find_packages

setup(
    name="calcul-dl-california",
    version="0.1.0",
    description="PDF417 / AAMVA tools and Streamlit demo",
    packages=find_packages(include=["pdf417gen", "pdf417gen.*"]),
    install_requires=[
        "requests>=2.28",
        "reportlab>=4.0",
        "streamlit>=1.0",
        "pytest>=7.0"
    ],
    python_requires=">=3.8",
    include_package_data=True,
)

"""
KSAT Math AI Setup Configuration
"""

from setuptools import setup, find_packages

with open("src/docs/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ksat-math-ai",
    version="2.0.0",
    author="KSAT Math AI Team",
    description="한국 수능 수학 문제 생성 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ksat-math-ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.25.0",
        "google-generativeai>=0.3.0",
        "sympy>=1.12",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "full": [
            "sentence-transformers>=2.2.0",
            "scikit-learn>=1.3.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ksat-math=src.ui.app:main",
        ],
    },
)
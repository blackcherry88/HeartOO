from setuptools import setup, find_packages

setup(
    name="heartoo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
        "matplotlib",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "heartpy",  # Optional for comparison
        ],
    },
    python_requires=">=3.7",
    description="Object-oriented heart rate analysis toolkit",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/heartoo",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)
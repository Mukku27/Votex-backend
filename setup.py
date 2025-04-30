from setuptools import setup, find_packages
from pathlib import Path

# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

# read requirements
requirements = []
with open(this_directory / "requirements.txt", encoding="utf-8") as req_file:
    requirements = [line.strip() for line in req_file if line.strip() and not line.startswith("#")]

setup(
    name="professor-feedback-analysis",
    version="1.0.0",
    author="Your Name",
    author_email="you@example.com",
    description="Backend API for analyzing student feedback using Groq LLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/professor-feedback-analysis",
    packages=find_packages(exclude=["tests*", "docs*"]),
    install_requires=requirements,
    python_requires=">=3.8",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            # You can run: feedback-api to start uvicorn
            "feedback-api=main:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Framework :: FastAPI",
        "Operating System :: OS Independent",
    ],
)

from setuptools import setup, find_packages
setup(
    name="job-hunter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["playwright","beautifulsoup4","pydantic","reportlab"],
    entry_points={"console_scripts": ["job-hunter=job_hunter.cli:main"]}
)

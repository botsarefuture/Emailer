from setuptools import setup, find_packages

setup(
    name="emailer",  # Package name
    version="0.1.0",  # Package version
    description="A module for managing and sending emails with templating and SMTP queue support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Verso Vuorenmaa",
    author_email="verso@luova.club",
    url="https://github.com/botsarefuture/Emailer/",  # URL to your project or repo
    license="MIT",  # License type
    packages=find_packages(),  # Automatically find all packages in the directory
    include_package_data=False,  # Include non-Python files (e.g., templates)
    install_requires=[
        "Jinja2>=3.0",
        "DatabaseManager=0.1"
    ],
    python_requires=">=3.6",  # Python version requirement
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

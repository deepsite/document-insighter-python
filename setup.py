from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="document-insighter",
    version="0.0.10",
    author="Wang Kai",
    author_email="wangkai@godeepsite.com",
    description="Document Insighter Python Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deepsite/document-insighter-python",
    project_urls={
        "Bug Tracker": "https://github.com/deepsite/document-insighter-python/issues"
    },
    license="MIT",
    packages=find_packages(exclude=("tests*",)),
    install_requires=["requests==2.31.0", "requests-oauthlib==1.3.1", "dataclasses-json==0.5.7", "polling2==0.5.0"],
)

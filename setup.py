import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='document-insighter',
    version='0.0.1',
    author='Wang Kai',
    author_email='wangkai@godeepsite.com',
    description='Document Insighter Python Client',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/deepsite/document-insighter-python',
    project_urls = {
        "Bug Tracker": "https://github.com/deepsite/document-insighter-python/issues"
    },
    license='MIT',
    packages=['document-insighter'],
    install_requires=['requests-oauthlib==1.3.1'],
)
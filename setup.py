import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyhomeworksqs",
    version="0.0.1",
    author="Ron Verstappen",
    author_email="ronverstappen@esample.com",
    description="Lutron Homeworks QS interface over telnet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rverstappen/pyhomeworksqs",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

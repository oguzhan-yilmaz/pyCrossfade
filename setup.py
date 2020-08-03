import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pycrossfade-oguzhan-yilmaz", # Replace with your own username
    version="0.0.1",
    author="Oğuzhan Yılmaz",
    author_email="oguzhanylmz271@gmail.com",
    description="A python package for audio programming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oguzhan-yilmaz/pyCrossfade",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
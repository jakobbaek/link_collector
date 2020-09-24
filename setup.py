import setuptools

def setup_this_lib():

    with open("README.md", "r") as fh:
        long_description = fh.read()

    setuptools.setup(
        name="spread-analysis", # Replace with your own username
        version="0.0.1",
        author="Jakob",
        author_email="jakob@ogtal.dk",
        description="Collect data and referals based on links. Analyse spread of links.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        install_requires=[
                "pandas",
                "selenium",
                "numpy",
                "TwitterAPI",
                "beautifulsoup4",
                "langdetect"
            ],
        python_requires='>=3.6',
    )

if __name__ == "__main__":
    setup_this_lib()

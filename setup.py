import setuptools


setuptools.setup(
    name = 'moi',
    version = "1.0.0",
    author = "Constantin Yves Lenoir",
    author_email = "constantinlenoir@gmail.com",
    description = 'An abstract rich text editor.',
    long_description= ('A text editor'
            ' which is abstract because of its command line interface'
            ' and rich because it can attach any format to a given string.'),
    long_description_content_type = 'text/txt',
    url = 'https://github.com/ConstantinLenoir/moi',
    packages = setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPL",
        "Operating System :: OS Independent",
    ],
    install_requires=[],
    python_requires='>=3.0',
    license = 'GNU GPL'
)

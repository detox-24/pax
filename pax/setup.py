from setuptools import setup

setup(
    name="paxer",
    version="1.0.1",
    packages=["pax"],
    install_requires=["click>=8.1.3", "paramiko>=3.4.0"],
    entry_points={"console_scripts": ["pax = pax.cli:cli"]},
    author="Sathiya Moorthi P",
    author_email="sathiyamoorthithuran@gmail.com",  
    description="Deploy .deb packages over SSH to multiple hosts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/detox-24/pax",  
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  
        "Operating System :: POSIX :: Linux",
    ],
)

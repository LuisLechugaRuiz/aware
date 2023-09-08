from setuptools import setup, find_packages

setup(
    name="aware",
    version="0.0.1",
    author="Luis Lechuga Ruiz",
    author_email="luislechugaruiz@gmail.com",
    description="Aware, here to help humans.",
    long_description=open("README.md").read(),
    url="https://github.com/LuisLechugaRuiz/aware",
    packages=find_packages(),
    license="MIT",
    classifiers=[],
    install_requires=open("requirements.txt").read().splitlines(),
    python_requires=">=3.10",
)

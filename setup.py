from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import shutil


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        # Call the standard install command
        install.run(self)

        # Now, perform the post-installation steps
        self.create_local_json_files()

    # TODO: refactor.
    def create_local_json_files(self):
        # Delayed import: Import your module here
        try:
            from aware.permanent_storage.permanent_storage import (
                get_permanent_storage_path,
            )
        except ImportError:
            print(
                "Could not import the module. Make sure your package is installed correctly."
            )
            return

        # Use your_module here to get paths or perform other actions
        json_files = {
            "user_profile_template.json": "user_profile.json",
            "working_memory_template.json": "working_memory.json",
        }
        json_directory = get_permanent_storage_path() / "user_data"

        for template, local in json_files.items():
            template_path = os.path.join(json_directory, template)
            local_path = os.path.join(json_directory, local)
            if not os.path.exists(local_path):
                shutil.copyfile(template_path, local_path)
                print(f"Created local copy: {local}")
            else:
                print(f"Local copy already exists: {local}")


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
    cmdclass={
        "install": PostInstallCommand,
    },
)

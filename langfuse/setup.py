from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-langfuse",
    version="1.0.0",
    description="CLI harness for the Langfuse LLM observability platform",
    long_description=open("cli_anything/langfuse/README.md").read(),
    long_description_content_type="text/markdown",
    author="cli-anything",
    license="MIT",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.langfuse": ["skills/*.md", "README.md"],
    },
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-langfuse=cli_anything.langfuse.langfuse_cli:main",
        ],
    },
    python_requires=">=3.10",
)

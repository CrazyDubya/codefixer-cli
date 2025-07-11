from setuptools import setup

setup(
    name='codefixer-cli',
    version='0.1.0',
    py_modules=['cli', 'languages', 'llm', 'git_utils', 'logger'],
    packages=['linters', 'templates'],
    install_requires=[
        'click>=8.0.0',
        'GitPython>=3.1.0',
        'tqdm>=4.64.0',
        'requests>=2.28.0',
        'flask>=2.0.0',
        'werkzeug>=2.0.0',
        'vllm>=0.2.0',
        'transformers>=4.20.0',
        'torch>=1.12.0',
    ],
    entry_points={
        'console_scripts': [
            'codefixer=cli:main',
        ],
    },
    include_package_data=True,
    description='Local-only CLI for automated code fixing with local LLM and best-practice linters.',
    author='Your Name',
    author_email='your@email.com',
    url='https://github.com/your/codefixer-cli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
) 
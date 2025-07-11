from setuptools import setup

setup(
    name='codefixer-cli',
    version='0.1.0',
    py_modules=['cli', 'languages', 'llm', 'git_utils', 'logger'],
    packages=['linters', 'templates'],
    install_requires=[
        'click',
        'GitPython',
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
from setuptools import setup


with open("README.rst") as readme_file:
    readme = readme_file.read()


setup(
    name='pytest-describe',
    version='2.0.0',
    description='Describe-style plugin for pytest',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/pytest-dev/pytest-describe',
    author='Robin Pedersen',
    author_email='robinpeder@gmail.com',
    license='MIT license',
    install_requires=[
        'pytest>=4.0.0',
    ],
    entry_points={
        'pytest11': [
            'pytest-describe = pytest_describe.plugin'
        ],
    },
    packages=['pytest_describe'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

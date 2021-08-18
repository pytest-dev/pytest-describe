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
    maintainer='Christoph Zwerschke',
    maintainer_email='cito@online.de',
    license='MIT',
    license_file='LICENSE',
    platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
    install_requires=[
        'pytest>=4.0.0',
    ],
    entry_points={
        'pytest11': [
            'pytest-describe = pytest_describe.plugin',
        ],
    },
    packages=['pytest_describe'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

from setuptools import setup


setup(
    name='pytest-describe',
    version='0.10.3',
    description='Describe-style plugin for pytest',
    url='https://github.com/ropez/pytest-describe',
    author='Robin Pedersen',
    author_email='robinpeder@gmail.com',
    license='MIT license',
    install_requires=[
        'pytest>=2.6.0',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)

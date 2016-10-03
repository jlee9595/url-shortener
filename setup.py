from setuptools import setup

setup(
    name='url_shortener',
    packages=['url_shortener'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
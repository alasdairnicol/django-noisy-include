from distutils.core import setup

setup(
    name='Django Noisy Include',
    version='0.1.0',
    author='Alasdsair Nicol',
    author_email='alasdair@thenicols.net',
    packages=['noisy_include'],
    license='LICENSE.txt',
    description='Noisy include tag for Django.',
    install_requires=[
        "Django >= 1.8",
    ],
)

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()
requirements = [item.strip() for item in requirements]

setup(
    name='udtk',
    version='0.1.dev0',
    description='UrbanSim Data Toolkit',
    author='UrbanSim Inc.',
    author_email='info@urbansim.com',
    url='https://github.com/udst/udtk',
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: BSD License'
    ],
    packages=find_packages(exclude=['*.tests']),
    install_requires=requirements
)

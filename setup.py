from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='mailpie',
    version='0.1',
    description='Send email from CLI with Python',
    long_description=readme(),
    url='http://github.com/guoqiao/mailpie',
    author='Guo Qiao',
    author_email='guoqiao@gmail.com',
    license='MIT',
    packages=['mailpie'],
    entry_points={
        'console_scripts': ['mailpie=mailpie.cli:main'],
    },
    zip_safe=False)

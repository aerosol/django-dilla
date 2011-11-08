from setuptools import setup, find_packages
from distribute_setup import use_setuptools
use_setuptools()


setup(
    name='django-dilla',
    version='0.2beta',
    author='Adam Rutkowski',
    author_email='adam@mtod.org',
    packages=find_packages(),
    url='http://aerosol.github.com/django-dilla/',
    license='BSD License',
    description='Ubercool database spammer for Django',
    long_description=open('README').read(),
    download_url='https://github.com/aerosol/django-dilla/',
    install_requires=['identicon'],
    dependency_links = [
        'https://github.com/aerosol/identicon/tarball/master#egg=identicon'
    ],
    classifiers = [
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                   'Topic :: Internet :: WWW/HTTP :: WSGI',
                   'Topic :: Software Development :: Libraries :: Application Frameworks',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Software Development :: Testing',
                   'Topic :: Utilities',
                   ]

)

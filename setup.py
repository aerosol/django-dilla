from distutils.core import setup


setup(
    name='django-dilla',
    version='0.2dev',
    author='Adam Rutkowski',
    author_email='adam@mtod.org',
    packages=['dilla',],
    url='http://aerosol.github.com/django-dilla/',
    license='BSD License',
    description='Ubercool database spammer for Django',
    long_description=open('README').read(),
    download_url='https://github.com/aerosol/django-dilla/tarball/master',
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

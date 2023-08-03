from setuptools import setup

setup(
    name='dvelopdmspy',
    version='1.0.3',
    description='d.velop DMS API wrapper for python',
    url='https://github.com/seb-bau/dvelop_dms_py',
    author='Sebastian Bauhaus',
    author_email='sebastian@bytewish.de',
    license='GPL-3.0',
    packages=['dvelopdmspy'],
    install_requires=['requests>=2.0',
                      'pyhumps>=3.0',
                      'jsonmerge>=1.9',
                      'pyhumps>=3.8'
                      ],

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],
)

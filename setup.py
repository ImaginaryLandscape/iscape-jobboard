from setuptools import setup, find_packages

version = '1.1'

setup(name='JobBoard',
      version=version,
      description="A simple job board for Django",
      long_description="""\
A simple job board for Django.
""",
      classifiers=[
        'Framework :: Django',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Development Status :: 4 - Beta'],
      keywords='django job board',
      author='Chris Webber',
      author_email='cwebber@imagescape.com',
      url='',
      license='GPL v3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      include_package_data=True,
      )


from setuptools import setup

setup(name='EqualAreaCartogram',
      version='0.1',
      description='Plot equal area cartograms',
      url='https://github.com/LokiTechnologies/EqualAreaCartogram',
      author='Rishabh Srivastava',
      author_email='rishabh@loki.ai',
      keywords=['cartography', 'data visualization', 'dataviz'],
      license='MIT',
      packages=['eqcart', 'chorogrid'],
      install_requires=['beautifulsoup4','pandas','geopandas'],
      zip_safe=False)
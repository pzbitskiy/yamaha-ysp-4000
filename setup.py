from setuptools import setup

with open('requirements.txt', encoding='utf-8') as req_fp:
    install_requires = req_fp.read().splitlines()


setup(name='yamaha-ysp-4000',
      version='0.2',
      url='http://github.com/pzbitskiy/yamaha-ysp-4000',
      license='MIT',
      packages=['ysp4000'],
      install_requires=install_requires,
      python_requires='>=3.10',
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'ysp4000-cmd = ysp4000.__main__:main',
          ]
      }
      )

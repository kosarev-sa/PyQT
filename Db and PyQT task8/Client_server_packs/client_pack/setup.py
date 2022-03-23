from setuptools import setup, find_packages

setup(name="sirius_mess_client",
      version="0.1",
      description="Client_pack",
      author="Sergey Kosarev",
      author_email="kosarev-sa@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )

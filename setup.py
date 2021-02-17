from setuptools import setup, find_packages

install_requires = [
    'omc>=0.2.3',
    'kubernetes>=11.0.0',
]

setup(
    name='omc-kube',
    version="0.0.4",
    description='kubenetes plugin for omc',
    license='MIT',
    author='Lu Ganlin',
    author_email='linewx1981@gmail.com',
    url='https://github.com/linewx/omc-kube',
    packages=find_packages(),
    package_data={'omc_kube.config': ['*.yaml'], 'omc_kube.lib': ['**', '**/*', '**/**/*']},
    install_requires=install_requires,
)

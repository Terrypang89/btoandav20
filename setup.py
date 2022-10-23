import setuptools
from distutils.util import convert_path

with open("README.md", "r") as fh:
    long_description = fh.read()

main_ns = {}
ver_path = convert_path('btoandav20/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setuptools.setup(
    name="btoandav20",
    version=main_ns['__version__'],
    description="Integrate Oanda-V20 API into backtrader",
    long_description=long_description,
    license='GNU General Public License Version 3',
    # url="https://github.com/happydasch/btoandav20",
    url="https://github.com/Terrypang89/btoandav20/tree/toufu_master",
    packages=setuptools.find_packages(),
    install_requires=[
        'backtrader>=1.9',
        'pyyaml',
        'v20'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.6'
)

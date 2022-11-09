from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in webshop/__init__.py
from webshop import __version__ as version

setup(
	name="webshop",
	version=version,
	description="Open Source eCommerce Platform",
	author="Frappe Technologies Pvt. Ltd.",
	author_email="contact@frappe.io",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

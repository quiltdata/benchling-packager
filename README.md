# benchling-packager

This repository generates a CloudFormation template for processing
[Benchling](https://benchling.com/) events in order create
(and link, if possible) a [Quilt](https://quiltdata.com/)
package for every Benchling notebook.

## Template generation

Requires a recent version of Python 3.

```shell
make template # creates a virtual environment to run make.py
ls build/benchling_packager.yaml
```

## Template upload

Currently it's distributed as a Quilt [package](https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager)
which is this way:

```python
quilt3.Package().set('README.md', 'install.md').set('benchling_packager.yaml', 'build/benchling_packager.yaml').push('examples/benchling-packager', 's3://quilt-example')
```

## Installation

To install and configure the template, see [Install.md](Install.md).
Note: this is the file that's distributed as `README.md` in the package.

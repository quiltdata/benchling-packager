# benchling-packager

## Template generation

Requires a recent version of Python 3.

```shell
python3 -m venv venv
. ./venv/bin/activate
python3 -m pip install -r requirements.txt
python3 make.py > build/benchling_packager.yml
```

Currently it's distributed as a Quilt [package](https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager)
which is this way:

```python
quilt3.Package().set('README.md', 'install.md').set('benchling_packager.yml', 'build/benchling_packager.yml').push('examples/benchling-packager', 's3://quilt-example')
```

## Installation

See [Install.md](Install.md).

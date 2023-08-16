# benchling-packager

This repository generates a CloudFormation template for processing
[Benchling](https://benchling.com/) events in order create
(and link, if possible) a [Quilt](https://quiltdata.com/)
package for every Benchling notebook.

## Template generation

Requires a recent version of Python 3.

```shell
python3 -m venv venv
. ./venv/bin/activate
python3 -m pip install -r requirements.txt
python3 make.py > build/benchling_packager.yaml
```

## Template upload

- setup the Python environment
- generate the template in the `build` directory
- upload the template to a Quilt package (if you have appropriate permissions)
- open the package URL: <https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager>

## Installation

To install and configure the template, see [Install.md](Install.md).
Note: this is the file that's distributed as `README.md` in the package.

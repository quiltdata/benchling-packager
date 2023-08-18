# benchling-packager

This repository generates a CloudFormation template for processing
[Benchling](https://benchling.com/) events in order create
(and link, if possible) a [Quilt](https://quiltdata.com/)
package for every Benchling notebook.

The code in this repository is open source under the [Apache 2.0 license](./LICENSE.txt).

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

## Testing for Developers

If you want to modify the actual lambda function, you can run automated tests via:

```shell
make test
```

In order to run these tests, you'll need to set the following environment variables
(usually in the `.env` file, which is auto-included by the Makefile):

- `BENCHLING_TENANT`: the part before ".benchling.com" in your Benchling URL (e.g. "mycompany" for "mycompany.benchling.com")
- `BENCHLING_CLIENT_ID`: the client ID for the Benchling API`
- `BENCHLING_CLIENT_SECRET_ARN`: the ARN of the AWS Secrets Manager secret containing the client secret for the Benchling API
- `DST_BUCKET`: the name of the S3 bucket (no prefix) where the generated packages should be stored
- `PKG_PREFIX`: the prefix to use for the generated packages, with a trailing "/" (e.g. "benchling/" to store packages in the "benchling" directory)
- `QUILT_CATALOG_DOMAIN`: the domain name of your Quilt catalog (if any) where the generated packages can be viewed

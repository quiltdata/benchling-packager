import quilt3

REGISTRY = "s3://quilt-example"
PKG_NAME = "examples/benchling-packager"
TEMPLATE = "benchling_packager.yaml"
TARGET = f"build/{TEMPLATE}"

def upload():
    pkg = quilt3.Package()
    pkg.set("README.md", "Install.md")
    pkg.set(TEMPLATE, TARGET)
    pkg.push(PKG_NAME, registry=REGISTRY)

if __name__ == "__main__":
    upload()

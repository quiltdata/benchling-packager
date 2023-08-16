TARGET = build/benchling_packager.yaml
ACTIVATE = ./venv/bin/activate
PKG_URL = "https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager"
.PHONY: all check-python39 clean install pip-compile template upload 

all: template upload

clean:
	rm -rf build
	rm -rf venv
	rm -f requirements.txt
	rm -f dev-requirements.txt

template: $(TARGET) 

build:
	mkdir -p build
upload:
	. $(ACTIVATE) && python3 upload.py
	open $(PKG_URL)

install: venv requirements.txt
	. $(ACTIVATE) && python3 -m pip install -r requirements.txt

$(TARGET): build install make.py lambdas/lambda.py
	. $(ACTIVATE) && python3 make.py > $(TARGET)

venv: check-python39
	python3.9 -m venv venv

check-python39:
	@python3.9 --version|| (echo "Python 3.9 required" && exit 1)

pip-compile: requirements.txt

requirements.txt: requirements.in 
	. $(ACTIVATE) && python3 -m pip install pip-tools
	. $(ACTIVATE) && pip-compile requirements.in
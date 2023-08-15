sinclude .env
TARGET = build/benchling_packager.yaml
ACTIVATE = ./venv/bin/activate
PKG_URL = "https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager"
.PHONY: all clean install pip-compile pip-dev template test upload

all: clean template upload

clean:
	rm -rf build
	rm -rf venv
	rm -f requirements.txt
	rm -f dev-requirements.txt

template: $(TARGET) 

upload:
	. $(ACTIVATE) && python3 upload.py
	open $(PKG_URL)

install: venv requirements.txt
#   . $(ACTIVATE) && python3 -m pip install -r requirements.txt
	. $(ACTIVATE) && pip-sync requirements.txt

$(TARGET): build install make.py lambdas/lambda.py
	. $(ACTIVATE) && python3 make.py > $(TARGET)

test: pip-dev run-test

run-test: venv
	. $(ACTIVATE) && python3 -m pytest

venv:
	python3 -m venv venv

build:
	mkdir build

tools: venv
	. $(ACTIVATE) && python3 -m pip install pip-tools

pip-compile: requirements.txt

requirements.txt: tools requirements.in
	. $(ACTIVATE) && pip-compile requirements.in

pip-dev: venv dev-requirements.txt
	. $(ACTIVATE) && pip-sync dev-requirements.txt

dev-requirements.txt: tools dev-requirements.in 
	. $(ACTIVATE) && pip-compile dev-requirements.in


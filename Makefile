sinclude .env
TARGET = build/benchling_packager.yaml
ACTIVATE = ./venv/bin/activate
PKG_URL = "https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager"
.PHONY: all check-python39 clean install pip-compile pip-dev template test upload 

all: template upload

clean:
	rm -rf build
	rm -rf venv
	rm -f requirements.txt
	rm -f dev-requirements.txt

template: $(TARGET) 

$(TARGET): build install make.py lambdas/main.py
	. $(ACTIVATE) && python3 make.py > $(TARGET)

upload:
	. $(ACTIVATE) && python3 upload.py
	open $(PKG_URL)

build:
	mkdir -p build

install: venv requirements.txt
	. $(ACTIVATE) && pip-sync requirements.txt

venv: check-python39
	python3.9 -m venv venv

check-python39:
	@python3.9 --version|| (echo "Python 3.9 required" && exit 1)

test: pip-dev run-test

run-test: venv
	. $(ACTIVATE) && python3 -m pytest

tools: venv
	. $(ACTIVATE) && python3 -m pip install pip-tools

pip-compile: requirements.txt

requirements.txt: tools requirements.in
	. $(ACTIVATE) && pip-compile requirements.in

pip-dev: venv dev-requirements.txt
	. $(ACTIVATE) && pip-sync dev-requirements.txt

dev-requirements.txt: tools dev-requirements.in 
	. $(ACTIVATE) && pip-compile dev-requirements.in


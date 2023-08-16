sinclude .env
TARGET = build/benchling_packager.yaml
ACTIVATE = ./venv/bin/activate
PKG_URL = "https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager"
.PHONY: all clean install install-dev template test upload 

all: template upload

clean:
	rm -rf build venv
	rm -f *requirements.txt .pytest_cache .DS_Store

template: $(TARGET) 

$(TARGET): build venv install make.py lambdas/main.py
	. $(ACTIVATE) && python3 make.py > $(TARGET)

upload:
	. $(ACTIVATE) && python3 upload.py
	open $(PKG_URL)

build:
	mkdir -p build

venv:
	@python3.9 --version|| (echo "Python 3.9 required" && exit 1)
	python3.9 -m venv venv

venv/bin/pip-compile:
	. $(ACTIVATE) && python3 -m pip install pip-tools

venv/bin/pip-sync:
	. $(ACTIVATE) && python3 -m pip install pip-tools

install: venv/bin/pip-sync requirements.txt
	. $(ACTIVATE) && pip-sync requirements.txt

requirements.txt: venv/bin/pip-compile requirements.in
	. $(ACTIVATE) && pip-compile requirements.in

test: venv install-dev
	. $(ACTIVATE) && python3 -m pytest  --cov --cov-report xml:coverage.xml

install-dev: venv/bin/pip-sync dev-requirements.txt
	. $(ACTIVATE) && pip-sync dev-requirements.txt

dev-requirements.txt: venv/bin/pip-sync dev-requirements.in 
	. $(ACTIVATE) && pip-compile dev-requirements.in


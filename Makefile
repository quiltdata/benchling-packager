TARGET = build/benchling_packager.yaml
ACTIVATE = ./venv/bin/activate
PKG_URL = "https://open.quiltdata.com/b/quilt-example/packages/examples/benchling-packager"
.PHONY: all template install pip-compile upload

all: template upload

template: $(TARGET) 

upload:
	. $(ACTIVATE) && python3 upload.py
	open $(PKG_URL)

install: venv requirements.txt
	. $(ACTIVATE) && python3 -m pip install -r requirements.txt

$(TARGET): install make.py lambdas/lambda.py
	. $(ACTIVATE) && python3 make.py > $(TARGET)

venv:
	python3 -m venv venv


pip-compile: requirements.txt

requirements.txt: requirements.in
	. $(ACTIVATE) && python3 -m pip install pip-tools
	. $(ACTIVATE) && pip-compile requirements.in
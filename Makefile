TARGET = build/benchling_packager.yaml
ACTIVATE = ./venv/bin/activate
.PHONY: all template

all: template

template: $(TARGET) 

$(TARGET): venv make.py lambdas/lambda.py
	. $(ACTIVATE) && python3 -m pip install -r requirements.txt
	. $(ACTIVATE) && python3 make.py > $(TARGET)

venv:
	python3 -m venv venv


pip-compile:
	. $(ACTIVATE) && python3 -m pip install pip-tools
	. $(ACTIVATE) && pip-compile requirements.in
TARGET=build/benchling_packager.yaml
.PHONY: all build

all: build

build: $(TARGET) 

$(TARGET): venv make.py lambdas/lambda.py
	./venv/bin/activate && python3 -m pip install -r requirements.txt
	./venv/bin/activate && python3 make.py > $(TARGET)

venv:
	python3 -m venv venv


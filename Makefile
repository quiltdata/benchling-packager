TARGET=build/template.yml
.PHONY: all

all: $(TARGET) 

$(TARGET): venv make.py lambdas/lambda.py
	. ./venv/bin/activate
	python3 -m pip install -r requirements.txt
	python3 make.py > build/template.yml

venv:
	python3 -m venv venv


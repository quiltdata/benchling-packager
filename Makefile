TARGET=build/template.yml
.PHONY: all

all: $(TARGET)
	python3 -m venv venv
	. ./venv/bin/activate
	python3 -m pip install -r requirements.txt
	python3 make.py > build/template.yml


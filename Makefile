.PHONY: all venv install build
PROJECT_NAME=benchling_packager.yaml
VENV=source venv/bin/activate

all: venv install build

# setup viritual environment

# Create virtual environment

venv:
	python3 -m venv venv
	
# Install dependencies

install:
	$(VENV) && python3 -m pip install --upgrade pip
	$(VENV) && pip install -r requirements.txt

# Build the template

build:
	$(VENV) && python3 make.py > $(PROJECT_NAME)


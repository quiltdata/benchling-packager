.PHONY: all template clean

PROJECT_NAME=benchling_packager.yaml
BUILD_DIR=build
BUILD_SENTINEL=$(BUILD_DIR)/.sentinel

PROJECT_FILE=$(BUILD_DIR)/$(PROJECT_NAME)
SRC=make.py

VENV=source venv/bin/activate

all: template

clean:
	rm -rf $(BUILD_DIR)
	rm -rf venv

# Create virtual environment

venv:
	python3 -m venv venv
	
# Install dependencies

setup: $(BUILD_SENTINEL)

 $(BUILD_SENTINEL): venv requirements.txt
	$(VENV) && python3 -m pip install --upgrade pip
	$(VENV) && pip install -r requirements.txt
	[ -d $(BUILD_DIR) ] || mkdir -p $(BUILD_DIR)
	touch $(BUILD_SENTINEL)

# Build the template

template: $(BUILD_SENTINEL) $(PROJECT_FILE)

$(PROJECT_FILE): $(SRC) lambdas/* layer/*
	$(VENV) && python3 $(SRC) > $(PROJECT_FILE)
	ls -lt $(PROJECT_FILE)


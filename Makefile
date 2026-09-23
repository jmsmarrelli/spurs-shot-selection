PY := python3

.PHONY: all build ahead clean site

all: build ahead

build:
	$(PY) src/run_01_build.py

ahead:
	$(PY) src/run_02_ahead.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install markdown`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv output/*.log data/processed/*

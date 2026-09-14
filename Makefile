PYTHON ?= python3

.PHONY: help test reproduce verify paper-source doctor paper package-source package

help:
	@echo "make reproduce      Audit saved evidence, reanalyze the pilot, check certificates and run tests (offline)"
	@echo "make test           Run the offline unit tests"
	@echo "make paper-source   Export the current manuscript as Markdown"
	@echo "make doctor         Check optional paper build dependencies (offline)"
	@echo "make paper          Build DOCX/PDF and page images when the paper toolchain is installed"
	@echo "make package-source Package repository sources and supplied PDFs without manuscript-build certification"
	@echo "make package        Package rendered paper and deck after their checks pass"

test:
	$(PYTHON) -m unittest discover -s tests -v

reproduce:
	$(PYTHON) scripts/reproduce.py

verify: reproduce

paper-source:
	$(PYTHON) scripts/export_markdown.py --out paper/manuscript.md

doctor:
	$(PYTHON) scripts/check_readiness.py --build-only

paper: paper-source
	$(PYTHON) scripts/build_paper.py

package-source: paper-source
	$(PYTHON) scripts/package_release.py --source-only

package: paper-source
	$(PYTHON) scripts/package_release.py

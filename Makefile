.PHONY: venv requirements test code-quality autochangelog

venv:
	rm -rf .venv
	python3.13 -m venv .venv

devready: venv
	.venv/bin/pip install -r requirements.txt
	@echo '###############################################################################'
	@echo '###  Do not forget to `source	.venv/bin/activate` to use this environment  ###'
	@echo '###############################################################################'

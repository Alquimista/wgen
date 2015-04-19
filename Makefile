init:
	pip2 install -r requirements.txt --use-mirrors

test:
	python wgen_test.py

docs: README.md
	pandoc -f markdown -t rst README.md > README.rst

requirements:
	pip freeze > requirements.txt & cat requirements.txt

build:
	python wgen.py

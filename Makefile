.PHONY: all	 clean  build	post


all: clean build post

clean:
	@echo "Cleaning build directories"
	@rm -rf ./build/* ./dist/* ./src/fastutils_hmarcuzzo.egg-info/* ./requirements.txt

build:
	@echo "Building package"
	@@pipenv run pipenv requirements --exclude-markers > requirements.txt
	@python3 setup.py sdist bdist_wheel

post:
	@echo "Uploading package to PyPI"
	@twine upload dist/*

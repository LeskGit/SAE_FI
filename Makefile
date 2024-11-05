.PHONY: clean
clean:  
	find . -type f -name "*.pyc" | xargs rm -fr  
	find . -type d -name __pycache__ | xargs rm -fr
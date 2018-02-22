ARGS = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

lint:
	rm -rf "src/__pycache__"
	python3 -m compileall src
	rm -rf "src/__pycache__"

commit: lint
	git add .
	git commit -m "$(call ARGS,\"updating to lastest local code\")"
	git push

%:
	@:

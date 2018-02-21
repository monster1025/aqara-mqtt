#SHELL := /bin/bash

ARGS = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

commit:
	git add .
	git commit -m "$(call ARGS,\"updating to lastest local code\")"
	git push

%:
    @:

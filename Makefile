NAME = inx-pathops

docs = \
	COPYING

source = \
	src/pathops.inx \
	src/pathops.py \
	src/pathops_cutpath.inx \
	src/pathops_difference.inx \
	src/pathops_division.inx \
	src/pathops_exclusion.inx \
	src/pathops_intersection.inx \

data =

# -----

ChangeLog.txt : $(docs) $(source) $(data)
	rm -f $@
	git log --oneline > $@

all = ChangeLog.txt $(docs) $(source) $(data)

revno = $(shell git rev-parse --short HEAD)
tag = $(shell git tag | tail -1)

.PHONY:	list
list:	$(all)
	@for i in $(all); do \
		echo $$i; \
	done

.PHONY:	zip
zip:	$(all)
	zip "$(NAME)-$(revno).zip" -X $(all)
	@echo "$(NAME)-$(revno).zip"

.PHONY: release
release: \
	$(all)
	zip "$(NAME)-$(tag).zip" -X $(all)
	@echo "$(NAME)-$(tag).zip"

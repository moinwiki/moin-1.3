POFILES = $(wildcard *.po)
UPDATEPOFILES = $(POFILES:.po=.po-update)
CATALOGS = $(POFILES:.po=.py)
NOPFILES = $(POFILES:.po=.nop)
DOMAIN = MoinMoin

.SUFFIXES: .py .po .po-update .nop

-include POTFILES

all: metapy

POTFILES: POTFILES.in
	@echo "POTFILES = \\" > POTFILES
	@sed -e '/^#/d' -e "/^[ ]*\$$/d" -e 's,.*,	../& \\,' -e '$$s/\(.*\) \\/\1/' < POTFILES.in >> POTFILES

.po.py:
	@echo "msgfmt -c --statistics $<"
	@msgfmt -c --statistics -o /dev/null $<
	@lang=`echo $@ | sed -e 's/\.py$$//'`; \
	echo build_lang_py $$lang; \
	./build_lang_py $$lang

.nop.po-update:
	@lang=`echo $@ | sed -e 's/\.po-update$$//'`; \
	echo "$$lang:"; \
	echo "msgmerge $$lang.po $(DOMAIN).pot -o $$lang.new.po"; \
	if msgmerge $$lang.po $(DOMAIN).pot -o $$lang.new.po; then \
	  if cmp $$lang.po $$lang.new.po >/dev/null 2>&1; then \
	    rm -f $$lang.new.po; \
	  else \
	    if mv -f $$lang.new.po $$lang.po; then \
	      :; \
	    else \
	      echo "msgmerge for $$lang.po failed: cannot move $$lang.new.po to $$lang.po" 1>&2; \
	      exit 1; \
	    fi; \
	  fi; \
	else \
	  echo "msgmerge for $$lang.po failed!" 1>&2; \
	  rm -f $$lang.new.po; \
	fi

$(DOMAIN).pot-update: $(POTFILES) POTFILES
	xgettext --default-domain=$(DOMAIN) --directory=.. \
	  --files-from=POTFILES.in \
	  --add-comments=TRANSLATORS:
	@test ! -f $(DOMAIN).po || { \
	  if test -f $(DOMAIN).pot; then \
	    sed -e 's/^"POT-Creation-Date: .*\"$$//' < $(DOMAIN).pot > $(DOMAIN).1po && \
	    sed -e 's/^"POT-Creation-Date: .*"$$//' < $(DOMAIN).po > $(DOMAIN).2po && \
	    if cmp $(DOMAIN).1po $(DOMAIN).2po >/dev/null 2>&1; then \
	      rm -f $(DOMAIN).1po $(DOMAIN).2po $(DOMAIN).po; \
	    else \
	      rm -f $(DOMAIN).1po $(DOMAIN).2po $(DOMAIN).pot && \
	      mv $(DOMAIN).po $(DOMAIN).pot; \
	    fi; \
	  else \
	    mv $(DOMAIN).po $(DOMAIN).pot; \
	  fi; \
	}

$(DOMAIN).pot:
	$(MAKE) $(DOMAIN).pot-update

$(POFILES): $(DOMAIN).pot
	@lang=`echo $@ | sed -e 's,.*/,,' -e 's/\.po$$//'`; \
	echo msgmerge --update $${lang}.po $(DOMAIN).pot; \
	msgmerge --update $${lang}.po $(DOMAIN).pot

$(NOPFILES):

metapy: $(CATALOGS)
	@langs=`echo $(CATALOGS) | sed -e 's/\.py//g'`; \
	./build_meta_py $$langs

update-po:
	$(MAKE) $(DOMAIN).pot-update
	$(MAKE) $(UPDATEPOFILES)
	$(MAKE) $(CATALOGS)
	$(MAKE) metapy

stats:
	@files="$(POFILES)"; \
	for i in $$files; do \
	  lang=`echo $$i | sed -e 's,.*/,,' -e 's/\.po$$//'`; \
	  echo -n "$$lang: "; \
	  msgfmt -o /dev/null --statistics $$i; \
	done

clean:
	rm POTFILES
	rm meta.wiki

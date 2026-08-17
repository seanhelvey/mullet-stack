.PHONY: html pdf clean

html:
	pandoc zine.md \
		--standalone \
		--css=style.css \
		--metadata title="The Mullet Stack" \
		-o zine.html

# Requires a TeX engine (e.g. `brew install basictex` on macOS,
# `apt install texlive-xetex` on Debian/Ubuntu).
pdf:
	pandoc zine.md \
		--pdf-engine=xelatex \
		-V geometry:margin=1in \
		-V colorlinks=true \
		-V mainfont="Georgia" \
		-o zine.pdf

clean:
	rm -f zine.html zine.pdf

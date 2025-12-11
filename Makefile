# GWiki Build System

SHELL := /bin/bash

# Directories
NOTES_DIR := notes
LIB_DIR := lib
BUILD_DIR := build
PDFS_DIR := pdfs
HTML_DIR := html
INDICES_DIR := indices

# LaTeX
LATEX := pdflatex
LATEXFLAGS := -interaction=nonstopmode -halt-on-error -output-directory=$(BUILD_DIR)

INDEX_TEX := index.tex
BIBLIOGRAPHY := references.bib

.PHONY: all clean new watch help index vault bibliography validate html web

all:
	@mkdir -p $(BUILD_DIR) $(PDFS_DIR)
	@python3 scripts/track-creation-dates.py > /dev/null 2>&1
	@chmod +x scripts/build-note.sh
	@count=0; \
	for f in $(NOTES_DIR)/*.tex; do \
		if [ -f "$$f" ]; then \
			name=$$(basename "$$f" .tex); \
			bash scripts/build-note.sh "$$f" "$(BUILD_DIR)"; \
			if [ -f "$(BUILD_DIR)/$$name.pdf" ]; then \
				mv "$(BUILD_DIR)/$$name.pdf" "$(PDFS_DIR)/$$name.pdf"; \
				echo "$$name"; \
				count=$$((count + 1)); \
			fi; \
		fi; \
	done; \
	echo ""; \
	echo "✓ $$count PDFs → $(PDFS_DIR)/"

vault: validate bibliography all index indices
	@note_count=$$(ls -1 $(PDFS_DIR)/*.pdf 2>/dev/null | wc -l | xargs); \
	note_count=$$((note_count - 1)); \
	echo ""; \
	echo "✓ Complete vault built"; \
	echo "  Notes: $$note_count PDFs in $(PDFS_DIR)/"; \
	echo "  Index: $(PDFS_DIR)/index.pdf"; \
	echo "  Bibliography: $(BIBLIOGRAPHY)"; \
	echo "  Master indices: $(INDICES_DIR)/"; \
	echo "  Build artifacts: $(BUILD_DIR)/"

web: all html
	@echo "✓ Web version ready at index.html"

html:
	@mkdir -p $(HTML_DIR)
	@echo "Converting notes to HTML..."
	@count=0; \
	for f in $(NOTES_DIR)/*.tex; do \
		if [ -f "$$f" ] && [[ ! "$$f" =~ (demo|debug) ]]; then \
			python3 scripts/tex-to-html.py "$$f" > /dev/null 2>&1; \
			count=$$((count + 1)); \
		fi; \
	done; \
	echo "  ✓ $$count HTML files → $(HTML_DIR)/"

indices:
	@echo "Generating master indices..."
	@python3 scripts/generate-master-index.py > /dev/null 2>&1
	@echo "  ✓ Master index → index.html"
	@echo "  ✓ LaTeX indices → $(INDICES_DIR)/"

index: $(INDEX_TEX)
	@mkdir -p $(BUILD_DIR) $(PDFS_DIR)
	@echo "Building index..."
	@TEXINPUTS=$(LIB_DIR): $(LATEX) $(LATEXFLAGS) $(INDEX_TEX) > /dev/null 2>&1
	@TEXINPUTS=$(LIB_DIR): $(LATEX) $(LATEXFLAGS) $(INDEX_TEX) > /dev/null 2>&1
	@mv $(BUILD_DIR)/index.pdf $(PDFS_DIR)/index.pdf 2>/dev/null || true
	@echo "  → $(PDFS_DIR)/index.pdf"

$(INDEX_TEX):
	@python3 scripts/track-creation-dates.py > /dev/null 2>&1
	@python3 scripts/generate-backlinks.py > /dev/null 2>&1
	@python3 scripts/generate-index.py

bibliography: $(BIBLIOGRAPHY)

$(BIBLIOGRAPHY):
	@python3 scripts/generate-bibliography.py

validate:
	@python3 scripts/validate-links.py

new:
ifndef NAME
	@echo "Usage: make new NAME=\"note title\""
else
	@mkdir -p $(NOTES_DIR)
	@python3 scripts/track-creation-dates.py > /dev/null 2>&1
	@if [ -f "$(NOTES_DIR)/$(NAME).tex" ]; then \
		echo "Error: $(NOTES_DIR)/$(NAME).tex already exists"; \
	else \
		echo '\\documentclass{gwiki}' > "$(NOTES_DIR)/$(NAME).tex"; \
		echo '' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '\\Title{$(NAME)}' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '\\Tags{}' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '\\begin{document}' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '\\NoteHeader' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '%% Content...' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '' >> "$(NOTES_DIR)/$(NAME).tex"; \
		echo '\\end{document}' >> "$(NOTES_DIR)/$(NAME).tex"; \
		python3 scripts/track-creation-dates.py > /dev/null 2>&1; \
		echo "✓ Created: $(NOTES_DIR)/$(NAME).tex"; \
	fi
endif

watch:
	@echo "Watching for changes... (Ctrl+C to stop)"
	@while true; do \
		inotifywait -q -e modify,create,delete -r $(NOTES_DIR) $(LIB_DIR) 2>/dev/null || sleep 2; \
		$(MAKE) all; \
	done

clean:
	@rm -rf build pdfs html indices index.tex index.html references.bib
	@rm -f $(NOTES_DIR)/*.aux $(NOTES_DIR)/*.log $(NOTES_DIR)/*.out $(NOTES_DIR)/*.toc $(NOTES_DIR)/*.bbl $(NOTES_DIR)/*.blg
	@rm -f *.aux *.log *.out *.toc *.bbl *.blg
	@echo "✓ Cleaned"

help:
	@echo "GWiki - LaTeX Note System"
	@echo "========================="
	@echo ""
	@echo "Common commands:"
	@echo "  make              Build all notes → pdfs/"
	@echo "  make vault        Build everything (validates, indices, bibliography)"
	@echo "  make web          Build web version (HTML + master index)"
	@echo "  make new NAME=\"note title\""
	@echo "  make clean        Remove all build artifacts"
	@echo ""
	@echo "Specialized commands:"
	@echo "  make html         Convert notes to HTML"
	@echo "  make indices      Generate master indices (HTML + LaTeX)"
	@echo "  make validate     Check for broken links"
	@echo "  make bibliography Generate bibliography from sources"
	@echo ""
	@echo "Output directories:"
	@echo "  pdfs/      PDF notes"
	@echo "  html/      HTML notes"
	@echo "  indices/   LaTeX indices (alphabetical, by-tag, chronological)"
	@echo "  build/     Auxiliary files"

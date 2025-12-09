# GWiki Build System - Simplified
# Just create .tex files in notes/ and run make

SHELL := /bin/bash

# Directories
NOTES_DIR := notes
LIB_DIR := lib
BUILD_DIR := build/pdf
PDFS_DIR := pdfs

# LaTeX
LATEX := pdflatex
LATEXFLAGS := -interaction=nonstopmode -halt-on-error

# Find all notes
SOURCES := $(wildcard $(NOTES_DIR)/*.tex)
PDFS := $(patsubst $(NOTES_DIR)/%.tex,$(BUILD_DIR)/%.pdf,$(SOURCES))
INDEX_TEX := index.tex
INDEX_PDF := $(BUILD_DIR)/index.pdf

# Default: build all
.PHONY: all clean new watch help index vault

all: $(PDFS)
	@echo "✓ Built $(words $(PDFS)) notes"

# Build complete vault (all notes + index)
vault: $(PDFS) index
	@mkdir -p $(PDFS_DIR)
	@cp -f $(BUILD_DIR)/*.pdf $(PDFS_DIR)/
	@echo "✓ Complete vault built → $(PDFS_DIR)/"
	@echo "  - $(words $(PDFS)) notes"
	@echo "  - 1 index"

# Build output directory
$(BUILD_DIR):
	@mkdir -p $@

# Build any note
$(BUILD_DIR)/%.pdf: $(NOTES_DIR)/%.tex $(LIB_DIR)/*.sty $(LIB_DIR)/*.cls | $(BUILD_DIR)
	@echo "Building: $*"
	@cd $(NOTES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) $(<F) > /dev/null 2>&1
	@cd $(NOTES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) $(<F) > /dev/null 2>&1
	@echo "  → $(BUILD_DIR)/$*.pdf"

# Generate and build vault index
index: $(INDEX_TEX)
	@echo "Building: index"
	@TEXINPUTS=$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=$(BUILD_DIR) $(INDEX_TEX) > /dev/null 2>&1
	@TEXINPUTS=$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=$(BUILD_DIR) $(INDEX_TEX) > /dev/null 2>&1
	@echo "  → $(BUILD_DIR)/index.pdf"

# Generate index.tex from notes
$(INDEX_TEX): $(SOURCES)
	@python3 scripts/generate-index.py

# Build single note by name
%: $(NOTES_DIR)/%.tex
	@$(MAKE) $(BUILD_DIR)/$*.pdf

# Create new note (simplest possible)
new:
ifndef NAME
	@echo "Usage: make new NAME=my-note"
	@echo "       make new NAME=my-note TITLE=\"My Note Title\""
else
	@mkdir -p $(NOTES_DIR)
	@if [ -f "$(NOTES_DIR)/$(NAME).tex" ]; then \
		echo "Error: $(NOTES_DIR)/$(NAME).tex already exists"; \
	else \
		echo '\\documentclass{gwiki}' > $(NOTES_DIR)/$(NAME).tex; \
		echo '' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '\\Title{$(or $(TITLE),$(NAME))}' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '\\Tags{}' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '\\begin{document}' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '\\NoteHeader' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '%% Your content here...' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '' >> $(NOTES_DIR)/$(NAME).tex; \
		echo '\\end{document}' >> $(NOTES_DIR)/$(NAME).tex; \
		echo "✓ Created: $(NOTES_DIR)/$(NAME).tex"; \
	fi
endif

# Watch and rebuild on changes
watch:
	@echo "Watching $(NOTES_DIR)/ for changes... (Ctrl+C to stop)"
	@while true; do \
		inotifywait -q -e modify,create,delete -r $(NOTES_DIR) $(LIB_DIR) 2>/dev/null || sleep 2; \
		$(MAKE) all; \
	done

# Clean
clean:
	@rm -rf build pdfs index.tex
	@rm -f $(NOTES_DIR)/*.aux $(NOTES_DIR)/*.log $(NOTES_DIR)/*.out $(NOTES_DIR)/*.toc
	@rm -f *.aux *.log *.out *.toc
	@echo "✓ Cleaned"

# Help
help:
	@echo "GWiki - LaTeX Note System"
	@echo "========================="
	@echo ""
	@echo "  make                    Build all notes"
	@echo "  make vault              Build all notes + index → pdfs/"
	@echo "  make index              Generate and build vault index"
	@echo "  make <name>             Build single note (e.g., make functor)"
	@echo "  make new NAME=xyz       Create new note"
	@echo "  make watch              Auto-rebuild on changes"
	@echo "  make clean              Remove build files"
	@echo ""
	@echo "Example workflow:"
	@echo "  make new NAME=category TITLE=\"Category\""
	@echo "  # edit notes/category.tex"
	@echo "  make vault              # Build everything"

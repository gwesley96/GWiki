# GWiki Build System - Simplified
# Just create .tex files in notes/ and run make

SHELL := /bin/bash

# Directories
NOTES_DIR := notes
LIB_DIR := lib
BUILD_DIR := build/pdf

# LaTeX
LATEX := pdflatex
LATEXFLAGS := -interaction=nonstopmode -halt-on-error

# Find all notes
SOURCES := $(wildcard $(NOTES_DIR)/*.tex)
PDFS := $(patsubst $(NOTES_DIR)/%.tex,$(BUILD_DIR)/%.pdf,$(SOURCES))

# Default: build all
.PHONY: all clean new watch help completions

all: $(PDFS)
	@echo "✓ Built $(words $(PDFS)) notes"

# Build output directory
$(BUILD_DIR):
	@mkdir -p $@

# Build any note
$(BUILD_DIR)/%.pdf: $(NOTES_DIR)/%.tex $(LIB_DIR)/*.sty $(LIB_DIR)/*.cls | $(BUILD_DIR)
	@echo "Building: $*"
	@cd $(NOTES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) $(<F) > /dev/null 2>&1
	@cd $(NOTES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) $(<F) > /dev/null 2>&1
	@echo "  → $(BUILD_DIR)/$*.pdf"

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
		$(MAKE) completions 2>/dev/null || true; \
	fi
endif

# Update VS Code completions
completions:
	@python3 scripts/generate-completions.py 2>/dev/null || echo "(completions script not found)"

# Watch and rebuild on changes
watch:
	@echo "Watching $(NOTES_DIR)/ for changes... (Ctrl+C to stop)"
	@while true; do \
		inotifywait -q -e modify,create,delete -r $(NOTES_DIR) $(LIB_DIR) 2>/dev/null || sleep 2; \
		$(MAKE) all; \
		$(MAKE) completions 2>/dev/null || true; \
	done

# Clean
clean:
	@rm -rf build
	@rm -f $(NOTES_DIR)/*.aux $(NOTES_DIR)/*.log $(NOTES_DIR)/*.out $(NOTES_DIR)/*.toc
	@echo "✓ Cleaned"

# Help
help:
	@echo "GWiki - LaTeX Note System"
	@echo "========================="
	@echo ""
	@echo "  make                    Build all notes"
	@echo "  make <name>             Build single note (e.g., make functor)"
	@echo "  make new NAME=xyz       Create new note"
	@echo "  make watch              Auto-rebuild on changes"
	@echo "  make clean              Remove build files"
	@echo ""
	@echo "Example workflow:"
	@echo "  make new NAME=category TITLE=\"Category\""
	@echo "  # edit notes/category.tex"
	@echo "  make category"

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
BIBER := biber

INDEX_TEX := index.tex

# Helper function to compile with optional biber
# Usage: $(call compile_latex,filename,source_dir)
define compile_latex
	@cd $(2) && TEXINPUTS=../$(LIB_DIR):../references: $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) "$(1).tex" > /dev/null 2>&1; \
	if [ -f "../$(BUILD_DIR)/$(1).bcf" ]; then \
		cd ../$(BUILD_DIR) && $(BIBER) "$(1)" > /dev/null 2>&1; \
		cd ../$(2) && TEXINPUTS=../$(LIB_DIR):../references: $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) "$(1).tex" > /dev/null 2>&1; \
	fi; \
	cd $(2) && TEXINPUTS=../$(LIB_DIR):../references: $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) "$(1).tex" > /dev/null 2>&1
endef

# Default: build all
.PHONY: all clean new watch help index vault

all:
	@mkdir -p $(BUILD_DIR)
	@count=0; \
	for f in $(NOTES_DIR)/*.tex; do \
		if [ -f "$$f" ]; then \
			name=$$(basename "$$f" .tex); \
			echo "Building: $$name"; \
			$(call compile_latex,$$name,$(NOTES_DIR)); \
			echo "  → $(BUILD_DIR)/$$name.pdf"; \
			count=$$((count + 1)); \
		fi; \
	done; \
	echo "✓ Built $$count notes"

# Build complete vault (all notes + index)
vault: all index
	@mkdir -p $(PDFS_DIR)
	@cp -f $(BUILD_DIR)/*.pdf $(PDFS_DIR)/
	@note_count=$$(ls -1 $(BUILD_DIR)/*.pdf 2>/dev/null | wc -l); \
	note_count=$$((note_count - 1)); \
	echo "✓ Complete vault built → $(PDFS_DIR)/"; \
	echo "  - $$note_count notes"; \
	echo "  - 1 index"

# Generate and build vault index
index: $(INDEX_TEX)
	@echo "Building: index"
	@TEXINPUTS=$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=$(BUILD_DIR) $(INDEX_TEX) > /dev/null 2>&1
	@TEXINPUTS=$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=$(BUILD_DIR) $(INDEX_TEX) > /dev/null 2>&1
	@echo "  → $(BUILD_DIR)/index.pdf"

# Generate index.tex from notes
$(INDEX_TEX):
	@python3 scripts/generate-index.py

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
	@rm -f $(BUILD_DIR)/*.aux $(BUILD_DIR)/*.log $(BUILD_DIR)/*.bcf $(BUILD_DIR)/*.blg $(BUILD_DIR)/*.bbl $(BUILD_DIR)/*.run.xml
	@rm -f *.aux *.log *.out *.toc *.bcf *.blg *.bbl *.run.xml
	@echo "✓ Cleaned"

# Pattern rule for building individual notes
%:
	@if [ -f "$(NOTES_DIR)/$@.tex" ]; then \
		mkdir -p $(BUILD_DIR); \
		echo "Building: $@"; \
		$(call compile_latex,$@,$(NOTES_DIR)); \
		echo "  → $(BUILD_DIR)/$@.pdf"; \
	else \
		echo "Error: $(NOTES_DIR)/$@.tex not found"; \
		exit 1; \
	fi

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

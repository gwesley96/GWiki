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

INDEX_TEX := index.tex

# Default: build all
.PHONY: all clean new watch help index vault

all:
	@mkdir -p $(BUILD_DIR)
	@count=0; \
	for f in $(NOTES_DIR)/*.tex; do \
		if [ -f "$$f" ]; then \
			name=$$(basename "$$f" .tex); \
			echo "Building: $$name"; \
			(cd $(NOTES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) "$$(basename "$$f")" > /dev/null 2>&1); \
			(cd $(NOTES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(BUILD_DIR) "$$(basename "$$f")" > /dev/null 2>&1); \
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

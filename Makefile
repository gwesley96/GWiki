# GWiki Build System
# Automated compilation of interconnected LaTeX notes
#
# Usage:
#   make              - Build all PDFs
#   make html         - Build all HTML (via lwarp)
#   make all          - Build both PDF and HTML
#   make article ID=xxx - Build single article
#   make wiki ID=xxx  - Build single wiki note
#   make new-article ID=xxx TITLE="Title" - Create new article
#   make new-wiki ID=xxx TITLE="Title" - Create new wiki note
#   make clean        - Remove build artifacts
#   make index        - Regenerate index files
#   make graph        - Generate dependency graph

SHELL := /bin/bash

# Directories
ARTICLES_DIR := articles
WIKI_DIR := wiki
LIB_DIR := lib
BUILD_DIR := build
PDF_DIR := $(BUILD_DIR)/pdf
HTML_DIR := $(BUILD_DIR)/html
SCRIPTS_DIR := scripts
INDEX_DIR := index
TEMPLATES_DIR := templates

# LaTeX settings
LATEX := pdflatex
LATEXFLAGS := -interaction=nonstopmode -halt-on-error -output-directory=$(PDF_DIR)
TEXINPUTS := .:$(LIB_DIR):

# lwarp settings for HTML
LWARPMK := lwarpmk

# Find all source files
ARTICLE_SOURCES := $(wildcard $(ARTICLES_DIR)/*.tex)
WIKI_SOURCES := $(wildcard $(WIKI_DIR)/*.tex)
ALL_SOURCES := $(ARTICLE_SOURCES) $(WIKI_SOURCES)

# Generate PDF targets
ARTICLE_PDFS := $(patsubst $(ARTICLES_DIR)/%.tex,$(PDF_DIR)/articles/%.pdf,$(ARTICLE_SOURCES))
WIKI_PDFS := $(patsubst $(WIKI_DIR)/%.tex,$(PDF_DIR)/wiki/%.pdf,$(WIKI_SOURCES))
ALL_PDFS := $(ARTICLE_PDFS) $(WIKI_PDFS)

# Generate HTML targets
ARTICLE_HTMLS := $(patsubst $(ARTICLES_DIR)/%.tex,$(HTML_DIR)/articles/%/index.html,$(ARTICLE_SOURCES))
WIKI_HTMLS := $(patsubst $(WIKI_DIR)/%.tex,$(HTML_DIR)/wiki/%/index.html,$(WIKI_SOURCES))
ALL_HTMLS := $(ARTICLE_HTMLS) $(WIKI_HTMLS)

# Default target
.PHONY: all pdf html clean index graph help watch new-article new-wiki

all: pdf html index

pdf: $(ALL_PDFS)
	@echo "✓ All PDFs built successfully"

html: $(ALL_HTMLS)
	@echo "✓ All HTML built successfully"

# Create output directories
$(PDF_DIR)/articles $(PDF_DIR)/wiki $(HTML_DIR)/articles $(HTML_DIR)/wiki:
	@mkdir -p $@

# Build article PDFs
$(PDF_DIR)/articles/%.pdf: $(ARTICLES_DIR)/%.tex $(LIB_DIR)/*.sty $(LIB_DIR)/*.cls | $(PDF_DIR)/articles
	@echo "Building article: $<"
	@cd $(ARTICLES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(PDF_DIR)/articles $(<F)
	@cd $(ARTICLES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(PDF_DIR)/articles $(<F)
	@echo "  → $(PDF_DIR)/articles/$*.pdf"

# Build wiki PDFs
$(PDF_DIR)/wiki/%.pdf: $(WIKI_DIR)/%.tex $(LIB_DIR)/*.sty $(LIB_DIR)/*.cls | $(PDF_DIR)/wiki
	@echo "Building wiki note: $<"
	@cd $(WIKI_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(PDF_DIR)/wiki $(<F)
	@cd $(WIKI_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) $(LATEXFLAGS) -output-directory=../$(PDF_DIR)/wiki $(<F)
	@echo "  → $(PDF_DIR)/wiki/$*.pdf"

# Build article HTML (via lwarp)
$(HTML_DIR)/articles/%/index.html: $(ARTICLES_DIR)/%.tex $(LIB_DIR)/*.sty $(LIB_DIR)/*.cls | $(HTML_DIR)/articles
	@echo "Building HTML for article: $<"
	@mkdir -p $(HTML_DIR)/articles/$*
	@cd $(ARTICLES_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) -jobname=$*_html "\def\uselwarp{1}\input{$(<F)}"
	@cd $(ARTICLES_DIR) && $(LWARPMK) html
	@cd $(ARTICLES_DIR) && $(LWARPMK) limages
	@mv $(ARTICLES_DIR)/$*_html*.html $(HTML_DIR)/articles/$*/
	@mv $(ARTICLES_DIR)/$*_html*.svg $(HTML_DIR)/articles/$*/ 2>/dev/null || true
	@echo "  → $(HTML_DIR)/articles/$*/"

# Build wiki HTML (via lwarp)
$(HTML_DIR)/wiki/%/index.html: $(WIKI_DIR)/%.tex $(LIB_DIR)/*.sty $(LIB_DIR)/*.cls | $(HTML_DIR)/wiki
	@echo "Building HTML for wiki note: $<"
	@mkdir -p $(HTML_DIR)/wiki/$*
	@cd $(WIKI_DIR) && TEXINPUTS=../$(LIB_DIR): $(LATEX) -jobname=$*_html "\def\uselwarp{1}\input{$(<F)}"
	@cd $(WIKI_DIR) && $(LWARPMK) html
	@cd $(WIKI_DIR) && $(LWARPMK) limages
	@mv $(WIKI_DIR)/$*_html*.html $(HTML_DIR)/wiki/$*/
	@mv $(WIKI_DIR)/$*_html*.svg $(HTML_DIR)/wiki/$*/ 2>/dev/null || true
	@echo "  → $(HTML_DIR)/wiki/$*/"

# Build single article by ID
article:
ifndef ID
	$(error Usage: make article ID=article-id)
endif
	@$(MAKE) $(PDF_DIR)/articles/$(ID).pdf

# Build single wiki note by ID
wiki:
ifndef ID
	$(error Usage: make wiki ID=wiki-id)
endif
	@$(MAKE) $(PDF_DIR)/wiki/$(ID).pdf

# Create new article from template
new-article:
ifndef ID
	$(error Usage: make new-article ID=article-id TITLE="Article Title")
endif
ifndef TITLE
	$(error Usage: make new-article ID=article-id TITLE="Article Title")
endif
	@$(SCRIPTS_DIR)/new-article.sh "$(ID)" "$(TITLE)"
	@echo "✓ Created new article: $(ARTICLES_DIR)/$(ID).tex"

# Create new wiki note from template
new-wiki:
ifndef ID
	$(error Usage: make new-wiki ID=wiki-id TITLE="Note Title")
endif
ifndef TITLE
	$(error Usage: make new-wiki ID=wiki-id TITLE="Note Title")
endif
	@$(SCRIPTS_DIR)/new-wiki.sh "$(ID)" "$(TITLE)"
	@echo "✓ Created new wiki note: $(WIKI_DIR)/$(ID).tex"

# Generate index files
index:
	@echo "Generating index..."
	@python3 $(SCRIPTS_DIR)/generate-index.py
	@echo "✓ Index generated"

# Generate dependency graph
graph:
	@echo "Generating dependency graph..."
	@python3 $(SCRIPTS_DIR)/generate-graph.py
	@echo "✓ Graph generated: $(BUILD_DIR)/graph.svg"

# Watch for changes and rebuild
watch:
	@echo "Watching for changes... (Ctrl+C to stop)"
	@while true; do \
		inotifywait -q -e modify -r $(ARTICLES_DIR) $(WIKI_DIR) $(LIB_DIR); \
		$(MAKE) pdf; \
	done

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -f $(ARTICLES_DIR)/*.aux $(ARTICLES_DIR)/*.log $(ARTICLES_DIR)/*.out
	@rm -f $(WIKI_DIR)/*.aux $(WIKI_DIR)/*.log $(WIKI_DIR)/*.out
	@rm -f $(ARTICLES_DIR)/*_html* $(WIKI_DIR)/*_html*
	@echo "✓ Clean complete"

# Deep clean (also removes generated index)
distclean: clean
	@rm -f $(INDEX_DIR)/*.json
	@echo "✓ Distribution clean complete"

# Help
help:
	@echo "GWiki Build System"
	@echo "=================="
	@echo ""
	@echo "Targets:"
	@echo "  make              - Build all PDFs (default)"
	@echo "  make html         - Build all HTML via lwarp"
	@echo "  make all          - Build both PDF and HTML"
	@echo "  make article ID=x - Build single article PDF"
	@echo "  make wiki ID=x    - Build single wiki note PDF"
	@echo "  make new-article ID=x TITLE=\"...\" - Create new article"
	@echo "  make new-wiki ID=x TITLE=\"...\"    - Create new wiki note"
	@echo "  make index        - Regenerate index files"
	@echo "  make graph        - Generate dependency graph"
	@echo "  make watch        - Watch and auto-rebuild on changes"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make distclean    - Remove all generated files"
	@echo ""
	@echo "Examples:"
	@echo "  make new-article ID=cat-theory-intro TITLE=\"Introduction to Category Theory\""
	@echo "  make article ID=cat-theory-intro"
	@echo "  make new-wiki ID=functor TITLE=\"Functor\""

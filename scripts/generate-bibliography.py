#!/usr/bin/env python3
"""
GWiki Bibliography Generator

Automatically generates BibTeX files from citations found in notes.

Scans all .tex notes for:
- \cite{key} commands
- \arxiv{id} commands
- @BibKey inline citations
- DOI URLs in \href commands

Fetches BibTeX entries from:
- arXiv API
- CrossRef API (for DOIs)
- Manual entries for nLab references

Usage:
  python3 generate-bibliography.py              # Generate references.bib
  python3 generate-bibliography.py --verbose    # Show detailed progress
"""

import re
import json
import sys
from pathlib import Path
from typing import Set, Optional, Dict
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent.parent
NOTES_DIR = ROOT / "notes"
OUTPUT_FILE = ROOT / "references.bib"

VERBOSE = "--verbose" in sys.argv


class CitationKey:
    """Represents a citation key with type information."""

    def __init__(self, key: str, source_type: str = "unknown"):
        self.key = key
        self.source_type = source_type

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, CitationKey) and self.key == other.key

    def __str__(self):
        return self.key


class CitationExtractor:
    """Extract citation keys from LaTeX notes."""

    PATTERNS = [
        # \cite{key} or \cite[text]{key}
        (r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}', 'cite'),

        # \arxiv{id}
        (r'\\arxiv\{([^}]+)\}', 'arxiv'),

        # \nlab{page}
        (r'\\nlab\{([^}]+)\}', 'nlab'),

        # @BibKey (but not \@, and not in comments)
        (r'(?:^|[^\\@])@([\w\-:]+)', 'inline'),

        # DOI in \href or \url
        (r'\\(?:href|url)\{[^}]*?doi\.org/(10\.\d+/[^\s}]+)\}', 'doi'),

        # arXiv URLs in \href or \url
        (r'\\(?:href|url)\{[^}]*?arxiv\.org/abs/([^}]+)\}', 'arxiv-url'),
    ]

    def extract_from_file(self, tex_file: Path) -> Set[CitationKey]:
        """Extract all citation keys from a single file."""
        try:
            content = tex_file.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            if VERBOSE:
                print(f"Warning: Could not read {tex_file}: {e}")
            return set()

        # Remove comments (lines starting with %)
        lines = []
        for line in content.splitlines():
            # Keep only content before % (unless \%)
            line = re.sub(r'(?<!\\)%.*$', '', line)
            lines.append(line)
        content = '\n'.join(lines)

        citations = set()

        for pattern, cite_type in self.PATTERNS:
            for match in re.finditer(pattern, content):
                key = match.group(1).strip()
                if key:
                    # Normalize arXiv IDs
                    if cite_type in ('arxiv', 'arxiv-url'):
                        key = self._normalize_arxiv_id(key)
                        cite_type = 'arxiv'

                    citations.add(CitationKey(key, cite_type))

        return citations

    def extract_from_notes(self, notes_dir: Path) -> Set[CitationKey]:
        """Extract all citation keys from all notes."""
        all_citations = set()

        for tex_file in sorted(notes_dir.glob("*.tex")):
            citations = self.extract_from_file(tex_file)
            if VERBOSE and citations:
                print(f"  {tex_file.stem}: {len(citations)} citations")
            all_citations.update(citations)

        return all_citations

    @staticmethod
    def _normalize_arxiv_id(arxiv_id: str) -> str:
        """Normalize arXiv ID to standard format."""
        # Remove version number (e.g., v1, v2)
        arxiv_id = re.sub(r'v\d+$', '', arxiv_id.strip())
        # Remove 'arXiv:' prefix if present
        arxiv_id = re.sub(r'^arXiv:', '', arxiv_id, flags=re.IGNORECASE)
        return arxiv_id


class BibTeXFetcher:
    """Fetch BibTeX entries from various sources."""

    def __init__(self):
        self.cache = {}
        self.failed = []

    def fetch(self, citation: CitationKey) -> Optional[str]:
        """Fetch BibTeX entry for a citation key."""
        if citation.key in self.cache:
            return self.cache[citation.key]

        try:
            if citation.source_type == 'arxiv':
                entry = self._fetch_arxiv(citation.key)
            elif citation.source_type == 'doi':
                entry = self._fetch_doi(citation.key)
            elif citation.source_type == 'nlab':
                entry = self._generate_nlab(citation.key)
            else:
                # For generic \cite{key}, create a stub entry
                entry = self._create_stub(citation.key)

            if entry:
                self.cache[citation.key] = entry
                return entry
        except Exception as e:
            if VERBOSE:
                print(f"  Failed to fetch {citation.key}: {e}")
            self.failed.append((citation.key, str(e)))

        return None

    def _fetch_arxiv(self, arxiv_id: str) -> Optional[str]:
        """Fetch BibTeX from arXiv API."""
        try:
            import arxiv
        except ImportError:
            if VERBOSE:
                print("  Note: Install 'arxiv' package for arXiv fetching: pip install arxiv")
            return self._create_arxiv_stub(arxiv_id)

        try:
            client = arxiv.Client()
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(client.results(search))

            # Build BibTeX entry
            authors = " and ".join(a.name for a in paper.authors)
            year = paper.published.year
            # Clean arXiv ID for BibTeX key (remove dots)
            bibtex_key = f"arXiv{arxiv_id.replace('.', '')}"

            entry = f"""@article{{{bibtex_key},
  author = {{{authors}}},
  title = {{{paper.title}}},
  year = {{{year}}},
  eprint = {{{arxiv_id}}},
  archivePrefix = {{arXiv}},
  primaryClass = {{{paper.primary_category}}},
  url = {{{paper.entry_id}}}
}}"""

            if VERBOSE:
                print(f"  ✓ Fetched arXiv:{arxiv_id}")

            return entry

        except Exception as e:
            if VERBOSE:
                print(f"  ! arXiv fetch failed for {arxiv_id}: {e}")
            return self._create_arxiv_stub(arxiv_id)

    def _fetch_doi(self, doi: str) -> Optional[str]:
        """Fetch BibTeX from CrossRef API."""
        try:
            import requests
        except ImportError:
            if VERBOSE:
                print("  Note: Install 'requests' for DOI fetching: pip install requests")
            return self._create_doi_stub(doi)

        try:
            url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
            headers = {'User-Agent': 'GWiki-BibliographyGenerator/1.0'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                if VERBOSE:
                    print(f"  ✓ Fetched DOI:{doi}")
                return response.text.strip()
            else:
                if VERBOSE:
                    print(f"  ! DOI fetch failed for {doi}: HTTP {response.status_code}")
                return self._create_doi_stub(doi)

        except Exception as e:
            if VERBOSE:
                print(f"  ! DOI fetch failed for {doi}: {e}")
            return self._create_doi_stub(doi)

    def _generate_nlab(self, page_name: str) -> str:
        """Generate @misc entry for nLab page."""
        bibtex_key = f"nLab{page_name.replace('-', '').replace(' ', '')}"
        title = page_name.replace('-', ' ').title()
        url = f"https://ncatlab.org/nlab/show/{page_name}"

        entry = f"""@misc{{{bibtex_key},
  title = {{{{nLab}}: {title}}},
  howpublished = {{\\url{{{url}}}}},
  note = {{Accessed: {datetime.now().strftime('%Y-%m-%d')}}}
}}"""

        if VERBOSE:
            print(f"  ✓ Generated nLab:{page_name}")

        return entry

    def _create_stub(self, key: str) -> str:
        """Create a stub BibTeX entry for unknown citations."""
        entry = f"""@misc{{{key},
  title = {{{key}}},
  note = {{TODO: Add full citation information}}
}}"""

        if VERBOSE:
            print(f"  ! Created stub for {key}")

        return entry

    def _create_arxiv_stub(self, arxiv_id: str) -> str:
        """Create stub for arXiv when fetching fails."""
        bibtex_key = f"arXiv{arxiv_id.replace('.', '')}"
        entry = f"""@article{{{bibtex_key},
  title = {{arXiv:{arxiv_id}}},
  eprint = {{{arxiv_id}}},
  archivePrefix = {{arXiv}},
  url = {{https://arxiv.org/abs/{arxiv_id}}},
  note = {{TODO: Fetch full metadata}}
}}"""
        return entry

    def _create_doi_stub(self, doi: str) -> str:
        """Create stub for DOI when fetching fails."""
        bibtex_key = f"doi{doi.replace('/', '').replace('.', '')}"
        entry = f"""@article{{{bibtex_key},
  title = {{DOI:{doi}}},
  doi = {{{doi}}},
  url = {{https://doi.org/{doi}}},
  note = {{TODO: Fetch full metadata}}
}}"""
        return entry


def generate_bibliography(notes_dir: Path, output_file: Path):
    """Main function to generate bibliography."""

    print("GWiki Bibliography Generator")
    print("=" * 50)

    # Extract citations
    print(f"\nScanning notes in {notes_dir}...")
    extractor = CitationExtractor()
    citations = extractor.extract_from_notes(notes_dir)

    print(f"Found {len(citations)} unique citations")

    if not citations:
        print("\nNo citations found. Nothing to generate.")
        return

    # Group by type
    by_type = defaultdict(list)
    for cit in citations:
        by_type[cit.source_type].append(cit)

    print("\nCitation breakdown:")
    for cite_type, cits in sorted(by_type.items()):
        print(f"  {cite_type}: {len(cits)}")

    # Fetch BibTeX entries
    print("\nFetching BibTeX entries...")
    fetcher = BibTeXFetcher()
    entries = []

    for citation in sorted(citations, key=lambda c: (c.source_type, c.key)):
        entry = fetcher.fetch(citation)
        if entry:
            entries.append(entry)

    # Write output
    header = f"""% GWiki Bibliography
% Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
% Total entries: {len(entries)}
%
% Do not edit manually - this file is regenerated automatically.
% To add/update citations, edit your notes and run: make bibliography

"""

    output_file.write_text(header + "\n\n".join(entries) + "\n", encoding='utf-8')

    print(f"\n✓ Generated bibliography: {output_file}")
    print(f"  - {len(entries)} entries")

    if fetcher.failed:
        print(f"\n⚠ {len(fetcher.failed)} citations failed to fetch (stubs created)")
        if VERBOSE:
            for key, error in fetcher.failed:
                print(f"    - {key}: {error}")

    print("\nDone!")


if __name__ == "__main__":
    generate_bibliography(NOTES_DIR, OUTPUT_FILE)

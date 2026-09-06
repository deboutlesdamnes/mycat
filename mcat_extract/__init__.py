# -*- coding: utf-8 -*-
"""Consolidated MCAT screenshot/corpus extraction pipeline."""
from .text import clean_ws, fix_ocr_artifacts, is_citation, HeaderParser, split_options
from .models import Passage, Question, Section
from .tables import TableReconstructor, table_to_markdown
from .builder import SectionBuilder
from .render import SECTION_SUBJECTS, Renderer
from .citations import CitationExtractor
from .openalex import Paper, OpenAlexClient, CorpusBuilder
from .claude import ClaudeCliClient
from .longform import (
    FigureSpec,
    QuestionSpec,
    PassageSpec,
    LONGFORM_PASSAGE_SYSTEM,
    build_passage_user,
)

__all__ = [
    "clean_ws",
    "fix_ocr_artifacts",
    "is_citation",
    "HeaderParser",
    "split_options",
    "Passage",
    "Question",
    "Section",
    "TableReconstructor",
    "table_to_markdown",
    "SectionBuilder",
    "SECTION_SUBJECTS",
    "Renderer",
    "CitationExtractor",
    "Paper",
    "OpenAlexClient",
    "CorpusBuilder",
    "ClaudeCliClient",
    "FigureSpec",
    "QuestionSpec",
    "PassageSpec",
    "LONGFORM_PASSAGE_SYSTEM",
    "build_passage_user",
]

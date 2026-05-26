"""
RAG V2 Format Adapters

Base adapter interface + concrete implementations for different file formats.
"""
from .base import BaseAdapter, RawChunk
from .code import CodeAdapter
from .markdown import MarkdownAdapter

__all__ = ["BaseAdapter", "RawChunk", "CodeAdapter", "MarkdownAdapter"]

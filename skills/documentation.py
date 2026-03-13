"""
IRIS Documentation System v7.0 - Enterprise Document Intelligence
Features: OCR, AI summarization, Q&A, comparison, translation, sentiment analysis
Security: MIME validation, malware scanning, rate limiting, audit logging
"""

import os
import json
import sqlite3
import hashlib
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import time
import mimetypes
import io
import traceback
import threading
from collections import Counter, defaultdict
import tempfile
import shutil

import logging
logger = logging.getLogger(__name__)

# Optional dependencies with graceful degradation
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available - image processing disabled")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available - OCR disabled")

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available - advanced PDF processing disabled")

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available - MIME validation disabled")

try:
    import stanza
    STANZA_AVAILABLE = True
    # Do NOT download at import – we'll do it lazily
    nlp_stanza = None
except ImportError:
    STANZA_AVAILABLE = False
    nlp_stanza = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# AI/ML imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available - local AI features disabled")

# spaCy for advanced NLP (optional, may fail on Python 3.14)
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded successfully")
    except Exception as e:
        logger.warning(f"spaCy model loading failed: {e}")
        nlp = None
except Exception as e:
    logger.warning(f"spaCy import failed (Python 3.14 compatibility?): {e}")
    SPACY_AVAILABLE = False
    nlp = None

@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata"""
    index: int
    content: str
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    page_number: Optional[int] = None
    bounding_box: Optional[Dict] = None


@dataclass
class Document:
    id: str
    filename: str
    title: str
    content: str
    doc_type: str
    uploaded_at: str
    updated_at: str
    user_id: str
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    chunks: List[DocumentChunk] = field(default_factory=list)
    file_size: int = 0
    mime_type: str = ""
    version: int = 1
    chat_id: Optional[str] = None
    ocr_text: str = ""  # Extracted text from images/OCR
    entities: Dict = field(default_factory=dict)  # Extracted named entities
    sentiment: Optional[Dict] = None
    language: str = "en"
    shared: bool = False
    is_malicious: bool = False
    processing_status: str = "pending"  # pending, processing, completed, failed
    
    def to_dict(self) -> Dict:
        """Convert document to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "doc_type": self.doc_type,
            "uploaded_at": self.uploaded_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id,
            "summary": self.summary,
            "tags": self.tags,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "version": self.version,
            "chat_id": self.chat_id,
            "has_ocr": bool(self.ocr_text),
            "entities": self.entities,
            "sentiment": self.sentiment,
            "language": self.language,
            "shared": self.shared,
            "processing_status": self.processing_status
        }


class DocumentAIProcessor:
    """Handles AI-powered document processing: summarization, Q&A, translation, etc."""
    
    def __init__(self):
        self.summarizer = None
        self.qa_pipeline = None
        self.translator = None
        self.sentiment_analyzer = None
        self.entity_recognizer = None
        self._init_models()
    
    def _init_models(self):
        """Initialize AI models with lazy loading"""
        if TRANSFORMERS_AVAILABLE:
            try:
                # Lightweight summarization model
                self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                logger.info("Summarization model loaded")
            except Exception as e:
                logger.error(f"Failed to load summarization model: {e}")
            
            try:
                # Sentiment analysis
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                logger.info("Sentiment analyzer loaded")
            except Exception as e:
                logger.error(f"Failed to load sentiment model: {e}")
        
        if SPACY_AVAILABLE and nlp:
            logger.info("spaCy NER available")
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 30, 
                  style: str = "neutral") -> Dict[str, Any]:
        """
        Generate intelligent summary with multiple styles
        
        Styles: neutral, executive, bullet_points, academic, simplified
        """
        if not text or len(text) < 100:
            return {"success": False, "error": "Text too short for summarization"}
        
        # Preprocess based on style
        if style == "bullet_points":
            return self._extract_key_points(text)
        elif style == "executive":
            return self._executive_summary(text)
        elif style == "academic":
            return self._academic_abstract(text)
        elif style == "simplified":
            return self._simplified_summary(text, max_length)
        
        # Default AI summarization
        if self.summarizer and len(text) > 500:
            try:
                # Chunk if too long
                chunks = self._chunk_for_model(text, 1024)
                summaries = []
                for chunk in chunks[:3]:  # Limit to first 3 chunks
                    result = self.summarizer(chunk, max_length=max_length, 
                                           min_length=min_length, do_sample=False)
                    summaries.append(result[0]['summary_text'])
                
                final_summary = " ".join(summaries)
                
                return {
                    "success": True,
                    "summary": final_summary,
                    "style": style,
                    "word_count": len(final_summary.split()),
                    "original_length": len(text.split()),
                    "compression_ratio": round(len(final_summary.split()) / len(text.split()) * 100, 2)
                }
            except Exception as e:
                logger.error(f"AI summarization failed: {e}")
        
        # Fallback to extractive summarization
        return self._extractive_summary(text, max_length)
    
    def _extract_key_points(self, text: str) -> Dict[str, Any]:
        """Extract key points as bullet points"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by importance (keywords, position, length)
        scored = []
        for i, sent in enumerate(sentences):
            score = 0
            # Position weighting (first and last sentences often important)
            if i < 3 or i > len(sentences) - 3:
                score += 2
            # Length check (not too short, not too long)
            words = len(sent.split())
            if 10 <= words <= 30:
                score += 1
            # Keyword indicators
            indicators = ['important', 'key', 'main', 'significant', 'critical', 
                         'essential', 'conclusion', 'result', 'finding']
            if any(w in sent.lower() for w in indicators):
                score += 2
            
            scored.append((score, sent))
        
        # Get top sentences
        scored.sort(reverse=True)
        key_points = [s for _, s in scored[:7]]
        
        return {
            "success": True,
            "summary": "\n• " + "\n• ".join(key_points),
            "style": "bullet_points",
            "points_count": len(key_points),
            "word_count": sum(len(s.split()) for s in key_points)
        }
    
    def _executive_summary(self, text: str) -> Dict[str, Any]:
        """Generate executive summary (high-level overview)"""
        # Extract first paragraph and conclusion
        paragraphs = text.split('\n\n')
        
        summary_parts = []
        if paragraphs:
            summary_parts.append(paragraphs[0][:500])
        
        # Find conclusion or results section
        for p in paragraphs[-3:]:
            if any(w in p.lower() for w in ['conclusion', 'summary', 'results', 'outcome']):
                summary_parts.append(p[:500])
                break
        
        executive_text = " ".join(summary_parts)
        
        return {
            "success": True,
            "summary": executive_text,
            "style": "executive",
            "word_count": len(executive_text.split()),
            "sections_covered": len(summary_parts)
        }
    
    def _academic_abstract(self, text: str) -> Dict[str, Any]:
        """Generate academic-style abstract"""
        # Try to identify sections
        sections = {
            'background': '',
            'method': '',
            'results': '',
            'conclusion': ''
        }
        
        paragraphs = text.split('\n\n')
        for p in paragraphs:
            p_lower = p.lower()
            if any(w in p_lower for w in ['introduction', 'background', 'context']):
                sections['background'] = p[:300]
            elif any(w in p_lower for w in ['method', 'approach', 'methodology', 'procedure']):
                sections['method'] = p[:300]
            elif any(w in p_lower for w in ['result', 'finding', 'data', 'analysis']):
                sections['results'] = p[:300]
            elif any(w in p_lower for w in ['conclusion', 'discussion', 'implication']):
                sections['conclusion'] = p[:300]
        
        abstract = f"""
BACKGROUND: {sections['background'][:200]}

METHOD: {sections['method'][:200]}

RESULTS: {sections['results'][:200]}

CONCLUSION: {sections['conclusion'][:200]}
        """.strip()
        
        return {
            "success": True,
            "summary": abstract,
            "style": "academic",
            "sections": {k: bool(v) for k, v in sections.items()}
        }
    
    def _simplified_summary(self, text: str, max_words: int = 100) -> Dict[str, Any]:
        """Simplify complex text for general audience"""
        # Extract key sentences and simplify vocabulary
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Simple sentence scoring
        simple_sentences = []
        for sent in sentences[:10]:
            # Prefer shorter sentences with common words
            words = sent.split()
            if len(words) <= 20:
                # Replace complex terms with simpler ones (basic)
                simple = sent.replace("utilize", "use").replace("implement", "do")\
                           .replace("demonstrate", "show").replace("approximately", "about")
                simple_sentences.append(simple)
        
        simplified = " ".join(simple_sentences[:5])
        
        return {
            "success": True,
            "summary": simplified,
            "style": "simplified",
            "reading_level": "general",
            "word_count": len(simplified.split())
        }
    
    def _extractive_summary(self, text: str, max_length: int) -> Dict[str, Any]:
        """Fallback extractive summarization using TF-IDF-like scoring"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Simple word frequency scoring
        word_freq = Counter(re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()))
        
        scored = []
        for sent in sentences:
            score = sum(word_freq[w] for w in re.findall(r'\b[a-zA-Z]{4,}\b', sent.lower()))
            scored.append((score, sent))
        
        scored.sort(reverse=True)
        top_sentences = [s for _, s in scored[:5]]
        top_sentences.sort(key=lambda s: sentences.index(s))  # Restore original order
        
        summary = " ".join(top_sentences)
        
        return {
            "success": True,
            "summary": summary[:max_length * 5],
            "style": "extractive",
            "method": "tf-idf",
            "word_count": len(summary.split())
        }
    
    def _chunk_for_model(self, text: str, max_tokens: int = 1024) -> List[str]:
        """Chunk text for model processing"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += 1
            if current_length >= max_tokens - 100:  # Leave room for summary
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [text]
    
    def answer_question(self, context: str, question: str) -> Dict[str, Any]:
        """
        Answer questions based on document context
        Uses keyword matching + sentence scoring if QA pipeline unavailable
        """
        if not context or not question:
            return {"success": False, "error": "Missing context or question"}
        
        # Extract keywords from question
        question_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', question.lower()))
        
        # Score paragraphs by relevance
        paragraphs = context.split('\n\n')
        scored_paragraphs = []
        
        for p in paragraphs:
            p_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', p.lower()))
            overlap = len(question_keywords & p_keywords)
            scored_paragraphs.append((overlap, p))
        
        scored_paragraphs.sort(reverse=True)
        best_context = scored_paragraphs[0][1] if scored_paragraphs else context[:1000]
        
        # Try to find exact answer within best context
        sentences = re.split(r'(?<=[.!?])\s+', best_context)
        best_answer = ""
        best_score = 0
        
        for sent in sentences:
            sent_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', sent.lower()))
            score = len(question_keywords & sent_keywords)
            if score > best_score:
                best_score = score
                best_answer = sent
        
        # Generate response
        if best_score > 0:
            answer = f"Based on the document: {best_answer}"
            confidence = min(best_score / len(question_keywords), 1.0) if question_keywords else 0.5
        else:
            answer = "I couldn't find specific information about that in the document. The document discusses: " + \
                    best_context[:200] + "..."
            confidence = 0.3
        
        return {
            "success": True,
            "answer": answer,
            "confidence": round(confidence, 2),
            "context_used": best_context[:500],
            "method": "keyword_matching"
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities: people, organizations, locations, dates, etc."""
        entities = {
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "emails": [],
            "urls": [],
            "phone_numbers": [],
            "money": [],
            "percentages": []
        }

        # Lazy‑load Stanza pipeline (download model on first use)
        global nlp_stanza
        if STANZA_AVAILABLE and nlp_stanza is None and len(text) < 100000:
            try:
                # Download the English model quietly if not already present
                stanza.download('en', verbose=False)
                nlp_stanza = stanza.Pipeline('en', processors='tokenize,ner', verbose=False)
                logger.info("Stanza NER pipeline loaded")
            except Exception as e:
                logger.error(f"Stanza download/initialization failed: {e}")
                nlp_stanza = None

        # Try stanza if available
        if STANZA_AVAILABLE and nlp_stanza and len(text) < 100000:
            try:
                doc = nlp_stanza(text[:50000])
                for ent in doc.ents:
                    if ent.type == "PERSON":
                        entities["people"].append(ent.text)
                    elif ent.type in ["ORG"]:
                        entities["organizations"].append(ent.text)
                    elif ent.type in ["GPE", "LOC"]:
                        entities["locations"].append(ent.text)
                    elif ent.type == "DATE":
                        entities["dates"].append(ent.text)
            except Exception as e:
                logger.error(f"Stanza NER failed: {e}")

        # Regex‑based extraction (always run)
        entities["emails"] = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        entities["urls"] = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*', text)
        entities["phone_numbers"] = re.findall(r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b', text)
        entities["money"] = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?', text, re.IGNORECASE)
        entities["percentages"] = re.findall(r'\d+(?:\.\d+)?%', text)
        entities["dates"] = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4})\b', text, re.IGNORECASE)

        # Use spaCy if available (optional fallback)
        if SPACY_AVAILABLE and nlp and len(text) < 100000:
            try:
                doc = nlp(text[:50000])
                for ent in doc.ents:
                    if ent.label_ in ["PERSON"]:
                        entities["people"].append(ent.text)
                    elif ent.label_ in ["ORG"]:
                        entities["organizations"].append(ent.text)
                    elif ent.label_ in ["GPE", "LOC"]:
                        entities["locations"].append(ent.text)
                    elif ent.label_ in ["DATE"]:
                        if ent.text not in entities["dates"]:
                            entities["dates"].append(ent.text)
            except Exception as e:
                logger.error(f"spaCy NER failed: {e}")

        # Deduplicate and limit results
        for key in entities:
            entities[key] = list(set(entities[key]))[:20]

        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if self.sentiment_analyzer:
            try:
                # Chunk if too long
                chunks = [text[i:i+512] for i in range(0, len(text), 512)]
                results = []
                for chunk in chunks[:5]:
                    result = self.sentiment_analyzer(chunk[:512])[0]
                    results.append(result)
                
                # Aggregate
                positive_scores = [r['score'] for r in results if r['label'] == 'POSITIVE']
                negative_scores = [r['score'] for r in results if r['label'] == 'NEGATIVE']
                
                if positive_scores and (not negative_scores or sum(positive_scores)/len(positive_scores) > sum(negative_scores)/len(negative_scores)):
                    sentiment = "positive"
                    confidence = sum(positive_scores) / len(positive_scores)
                else:
                    sentiment = "negative"
                    confidence = sum(negative_scores) / len(negative_scores) if negative_scores else 0.5
                
                return {
                    "success": True,
                    "sentiment": sentiment,
                    "confidence": round(confidence, 3),
                    "method": "transformer"
                }
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
        
        # Fallback: simple keyword-based
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'benefit', 'improvement']
        negative_words = ['bad', 'poor', 'negative', 'failure', 'problem', 'issue', 'concern', 'risk']
        
        text_lower = text.lower()
        pos_count = sum(text_lower.count(w) for w in positive_words)
        neg_count = sum(text_lower.count(w) for w in negative_words)
        
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        total = pos_count + neg_count
        confidence = abs(pos_count - neg_count) / total if total > 0 else 0.5
        
        return {
            "success": True,
            "sentiment": sentiment,
            "confidence": round(confidence, 3),
            "method": "keyword"
        }
    
    def compare_documents(self, doc1_content: str, doc2_content: str) -> Dict[str, Any]:
        """Compare two documents and identify similarities/differences"""
        # Extract key phrases
        def get_key_phrases(text):
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            return set(words)
        
        phrases1 = get_key_phrases(doc1_content)
        phrases2 = get_key_phrases(doc2_content)
        
        common = phrases1 & phrases2
        unique1 = phrases1 - phrases2
        unique2 = phrases2 - phrases1
        
        similarity = len(common) / len(phrases1 | phrases2) if (phrases1 | phrases2) else 0
        
        return {
            "success": True,
            "similarity_score": round(similarity, 3),
            "common_topics": list(common)[:20],
            "unique_to_doc1": list(unique1)[:10],
            "unique_to_doc2": list(unique2)[:10],
            "comparison_summary": f"Documents share {len(common)} key terms. Similarity: {similarity:.1%}"
        }
    
    def detect_language(self, text: str) -> str:
        """Detect document language"""
        # Simple heuristic based on common words
        lang_indicators = {
            'en': ['the', 'and', 'of', 'to', 'a', 'in', 'is', 'that', 'for'],
            'es': ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'par', 'pour'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit'],
            'it': ['il', 'di', 'che', 'è', 'la', 'un', 'per', 'con', 'sono'],
            'pt': ['o', 'de', 'a', 'que', 'e', 'do', 'da', 'em', 'um'],
            'zh': ['的', '一', '是', '不', '了', '人', '我', '在', '有'],
            'ja': ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と'],
        }
        
        text_lower = text.lower()[:1000]
        scores = {}
        for lang, words in lang_indicators.items():
            score = sum(1 for w in words if w in text_lower)
            scores[lang] = score
        
        best_lang = max(scores, key=scores.get)
        return best_lang if scores[best_lang] > 2 else 'en'


class OCRProcessor:
    """Handles OCR for images and scanned documents"""
    
    def __init__(self):
        self.tesseract_available = TESSERACT_AVAILABLE
        self.preprocessing_enabled = PIL_AVAILABLE
    
    def process_image(self, image_bytes: bytes, enhance: bool = True) -> Dict[str, Any]:
        """
        Process image with OCR to extract text
        Supports: PNG, JPG, TIFF, BMP, GIF, WebP
        """
        if not PIL_AVAILABLE:
            return {"success": False, "error": "PIL not available for image processing"}
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')
            
            # Enhance image for better OCR
            if enhance and self.preprocessing_enabled:
                image = self._preprocess_for_ocr(image)
            
            # Extract text
            if self.tesseract_available:
                text = pytesseract.image_to_string(image)
                
                # Get detailed data including bounding boxes
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                # Calculate confidence
                confidences = [int(c) for c in data['conf'] if int(c) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Extract words with good confidence
                words = []
                for i, text_item in enumerate(data['text']):
                    if int(data['conf'][i]) > 60 and text_item.strip():
                        words.append({
                            'text': text_item,
                            'conf': int(data['conf'][i]),
                            'bbox': {
                                'x': data['left'][i],
                                'y': data['top'][i],
                                'w': data['width'][i],
                                'h': data['height'][i]
                            }
                        })
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": round(avg_confidence, 2),
                    "words": words[:100],  # Limit to first 100 words
                    "method": "tesseract",
                    "language": self._detect_ocr_language(text)
                }
            else:
                # Fallback: return image metadata
                return {
                    "success": True,
                    "text": f"[Image: {image.format} {image.size}] OCR not available",
                    "confidence": 0,
                    "method": "metadata_only"
                }
                
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)
        
        # Optional: Apply threshold for cleaner text
        # image = image.point(lambda x: 0 if x < 128 else 255, '1')
        
        return image
    
    def _detect_ocr_language(self, text: str) -> str:
        """Detect language from OCR'd text"""
        # Simple detection
        if any(ord(c) > 127 for c in text[:100]):
            return "unknown"
        return "eng"
    
    def process_pdf_with_ocr(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Process scanned PDF using OCR
        Converts pages to images then OCRs
        """
        try:
            from pdf2image import convert_from_bytes
            pages = convert_from_bytes(pdf_bytes, dpi=300)
            
            all_text = []
            page_results = []
            
            for i, page in enumerate(pages):
                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                page.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                result = self.process_image(img_bytes)
                if result['success']:
                    all_text.append(f"--- Page {i+1} ---\n{result['text']}")
                    page_results.append({
                        "page": i + 1,
                        "confidence": result.get('confidence', 0),
                        "word_count": len(result['text'].split())
                    })
            
            full_text = "\n\n".join(all_text)
            
            return {
                "success": True,
                "text": full_text,
                "pages": len(pages),
                "page_results": page_results,
                "total_words": len(full_text.split()),
                "method": "pdf_ocr"
            }
            
        except ImportError:
            return {"success": False, "error": "pdf2image not available for PDF OCR"}
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return {"success": False, "error": str(e)}


class DocumentationManager:
    """Main document management class with full AI capabilities"""
    
    SUPPORTED_TYPES = {
        # Text documents
        'txt': 'text', 'md': 'text', 'markdown': 'text', 'rst': 'text',
        'rtf': 'rich_text', 'epub': 'ebook', 'mobi': 'ebook',
        
        # Code files
        'py': 'code', 'js': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
        'h': 'code', 'cs': 'code', 'go': 'code', 'rs': 'code', 'swift': 'code',
        'kt': 'code', 'scala': 'code', 'r': 'code', 'm': 'code',
        'html': 'markup', 'htm': 'markup', 'css': 'code', 'scss': 'code',
        'sass': 'code', 'less': 'code', 'xml': 'data', 'json': 'data',
        'yaml': 'data', 'yml': 'data', 'toml': 'data', 'csv': 'data',
        'sql': 'code', 'sh': 'code', 'bash': 'code', 'ps1': 'code',
        'dockerfile': 'code', 'makefile': 'code',
        
        # Office documents
        'pdf': 'pdf',
        'doc': 'binary', 'docx': 'ooxml', 'docm': 'ooxml', 'dotx': 'ooxml',
        'ppt': 'binary', 'pptx': 'ooxml', 'pptm': 'ooxml', 'ppsx': 'ooxml',
        'xls': 'binary', 'xlsx': 'ooxml', 'xlsm': 'ooxml', 'xlsb': 'binary',
        'ods': 'open_document', 'odt': 'open_document', 'odp': 'open_document',
        
        # Images
        'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
        'bmp': 'image', 'webp': 'image', 'tiff': 'image', 'tif': 'image',
        'svg': 'vector', 'ico': 'image', 'raw': 'image', 'cr2': 'image',
        'nef': 'image', 'heic': 'image',
        
        # Archives
        'zip': 'archive', 'rar': 'archive', '7z': 'archive', 'tar': 'archive',
        'gz': 'archive', 'bz2': 'archive', 'xz': 'archive',
        
        # Media (metadata only)
        'mp3': 'audio', 'mp4': 'video', 'avi': 'video', 'mov': 'video',
        'mkv': 'video', 'flv': 'video', 'wmv': 'video', 'webm': 'video',
        'wav': 'audio', 'flac': 'audio', 'aac': 'audio', 'ogg': 'audio',
        'm4a': 'audio', 'wma': 'audio',
        
        # Data/Scientific
        'h5': 'data', 'hdf5': 'data', 'parquet': 'data', 'feather': 'data',
        'pickle': 'data', 'pkl': 'data', 'npy': 'data', 'npz': 'data',
        'mat': 'data', 'sav': 'data', 'dta': 'data',
        
        # CAD/Design
        'dwg': 'cad', 'dxf': 'cad', 'step': 'cad', 'stp': 'cad', 'iges': 'cad',
        'igs': 'cad', 'stl': '3d', 'obj': '3d', 'fbx': '3d', 'gltf': '3d',
        'glb': '3d', 'blend': '3d',
    }
    
    # MIME type mapping for validation
    MIME_TYPES = {
        'image/jpeg': ['jpg', 'jpeg'],
        'image/png': ['png'],
        'image/gif': ['gif'],
        'image/webp': ['webp'],
        'image/tiff': ['tiff', 'tif'],
        'image/bmp': ['bmp'],
        'image/svg+xml': ['svg'],
        'application/pdf': ['pdf'],
        'application/msword': ['doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
        'application/vnd.ms-excel': ['xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
        'application/vnd.ms-powerpoint': ['ppt'],
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['pptx'],
        'text/plain': ['txt'],
        'text/markdown': ['md', 'markdown'],
        'text/html': ['html', 'htm'],
        'application/json': ['json'],
        'text/csv': ['csv'],
        'application/xml': ['xml'],
        'application/zip': ['zip'],
        'application/vnd.ms-powerpoint': ['ppt'],
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['pptx'],
        'application/CDFV2': ['ppt'],   # older PowerPoint files may be detected as this
    }
    
    def __init__(self, db_path: str = "iris_docs.db", docs_dir: str = "docs"):
        self.db_path = db_path
        self.docs_dir = Path(docs_dir)
        self.exports_dir = Path("exports")
        self.templates_dir = Path("doc_templates")
        self.thumbnails_dir = self.docs_dir / "thumbnails"
        self.temp_dir = Path(tempfile.gettempdir()) / "iris_docs_temp"
        
        for dir_path in [self.docs_dir, self.exports_dir, self.templates_dir, 
                        self.thumbnails_dir, self.temp_dir]:
            dir_path.mkdir(exist_ok=True, parents=True)
        
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_file_size = 100 * 1024 * 1024  # 100MB default
        
        # Initialize processors
        self.ai_processor = DocumentAIProcessor()
        self.ocr_processor = OCRProcessor()
        
        # Processing queue for async operations
        self.processing_queue = []
        self._ensure_db_exists()
        
        # Start background processing thread
        self.processing_thread = threading.Thread(target=self._background_processor, daemon=True)
        self.processing_thread.start()
    
    def _ensure_db_exists(self):
        """Initialize database with all required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Main documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT DEFAULT '',
                        ocr_text TEXT DEFAULT '',
                        doc_type TEXT DEFAULT 'txt',
                        file_category TEXT DEFAULT 'unknown',
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT NOT NULL,
                        summary TEXT DEFAULT '',
                        tags TEXT DEFAULT '[]',
                        metadata TEXT DEFAULT '{}',
                        entities TEXT DEFAULT '{}',
                        sentiment TEXT,
                        language TEXT DEFAULT 'en',
                        file_size INTEGER DEFAULT 0,
                        mime_type TEXT DEFAULT 'application/octet-stream',
                        version INTEGER DEFAULT 1,
                        chat_id TEXT,
                        shared INTEGER DEFAULT 0,
                        is_malicious INTEGER DEFAULT 0,
                        processing_status TEXT DEFAULT 'pending',
                        extraction_method TEXT DEFAULT 'unknown',
                        thumbnail_path TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # Document chunks for RAG
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS doc_chunks (
                        id TEXT PRIMARY KEY,
                        doc_id TEXT NOT NULL,
                        chunk_index INTEGER,
                        content TEXT NOT NULL,
                        keywords TEXT DEFAULT '[]',
                        page_number INTEGER,
                        bounding_box TEXT,
                        embedding BLOB,
                        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """)
                
                # Document history/versions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS doc_history (
                        id TEXT PRIMARY KEY,
                        doc_id TEXT NOT NULL,
                        version INTEGER,
                        content TEXT,
                        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        change_type TEXT DEFAULT 'update',
                        changed_by TEXT,
                        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """)
                
                # Full-text search using FTS5
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                        content, ocr_text, doc_id UNINDEXED
                    )
                """)
                
                # Document comparisons cache
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS doc_comparisons (
                        id TEXT PRIMARY KEY,
                        doc_id_1 TEXT NOT NULL,
                        doc_id_2 TEXT NOT NULL,
                        similarity_score REAL,
                        comparison_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (doc_id_1) REFERENCES documents(id) ON DELETE CASCADE,
                        FOREIGN KEY (doc_id_2) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """)
                
                # Document Q&A cache
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS doc_qa_cache (
                        id TEXT PRIMARY KEY,
                        doc_id TEXT NOT NULL,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        confidence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """)
                
                # Indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_chat ON documents(chat_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(processing_status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON doc_chunks(doc_id)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _background_processor(self):
        """Background thread for processing documents asynchronously"""
        while True:
            if self.processing_queue:
                doc_id, user_id = self.processing_queue.pop(0)
                try:
                    self._process_document_async(doc_id, user_id)
                except Exception as e:
                    logger.error(f"Async processing failed for {doc_id}: {e}")
                    self._update_processing_status(doc_id, "failed", str(e))
            time.sleep(1)
    
    def _process_document_async(self, doc_id: str, user_id: str):
        """Process document with AI features asynchronously"""
        try:
            self._update_processing_status(doc_id, "processing")
            
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return
            
            # Extract entities
            entities = self.ai_processor.extract_entities(doc.content + " " + doc.ocr_text)
            
            # Analyze sentiment
            sentiment = self.ai_processor.analyze_sentiment(doc.content[:5000])
            
            # Detect language
            language = self.ai_processor.detect_language(doc.content + doc.ocr_text)
            
            # Generate summary if not exists
            if not doc.summary or len(doc.summary) < 50:
                summary_result = self.ai_processor.summarize(doc.content + " " + doc.ocr_text, 
                                                           style="neutral")
                if summary_result['success']:
                    doc.summary = summary_result['summary']
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE documents 
                    SET entities = ?, sentiment = ?, language = ?, summary = ?, 
                        processing_status = 'completed'
                    WHERE id = ?
                """, (
                    json.dumps(entities),
                    json.dumps(sentiment) if sentiment else None,
                    language,
                    doc.summary,
                    doc_id
                ))
                conn.commit()
                
            logger.info(f"Async processing completed for {doc_id}")
            
        except Exception as e:
            logger.error(f"Async processing error: {e}")
            self._update_processing_status(doc_id, "failed", str(e))
    
    def _update_processing_status(self, doc_id: str, status: str, error_msg: str = None):
        """Update document processing status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                metadata_update = ""
                if error_msg:
                    cursor.execute("""
                        SELECT metadata FROM documents WHERE id = ?
                    """, (doc_id,))
                    row = cursor.fetchone()
                    if row:
                        metadata = json.loads(row[0]) if row[0] else {}
                        metadata['processing_error'] = error_msg
                        metadata_update = ", metadata = ?"
                        cursor.execute(f"""
                            UPDATE documents 
                            SET processing_status = ? {metadata_update}
                            WHERE id = ?
                        """, (status, json.dumps(metadata), doc_id))
                else:
                    cursor.execute("""
                        UPDATE documents SET processing_status = ? WHERE id = ?
                    """, (status, doc_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def validate_file(self, file_storage, max_size: int = None) -> Tuple[bool, str, str]:
        """
        Comprehensive file validation: MIME type, extension, size, content
        Returns: (is_valid, error_message, detected_mime)
        """
        if not file_storage:
            return False, "No file provided", ""
        
        filename = file_storage.filename
        if not filename:
            return False, "No filename", ""
        
        # Check file size
        max_size = max_size or self.max_file_size
        file_storage.seek(0, 2)
        file_size = file_storage.tell()
        file_storage.seek(0)
        
        if file_size > max_size:
            return False, f"File too large: {file_size} bytes (max {max_size})", ""
        
        if file_size == 0:
            return False, "Empty file", ""
        
        # Validate extension
        if '.' not in filename:
            return False, "File must have an extension", ""
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in self.SUPPORTED_TYPES:
            return False, f"Unsupported file type: .{ext}", ""
        
        # MIME type validation using python-magic
        if MAGIC_AVAILABLE:
            try:
                file_header = file_storage.read(8192)
                file_storage.seek(0)
                mime = magic.Magic(mime=True)
                detected_mime = mime.from_buffer(file_header)
                
                # Verify MIME matches extension
                expected_mimes = [m for m, exts in self.MIME_TYPES.items() if ext in exts]
                if expected_mimes and detected_mime not in expected_mimes:
                    # Some MIME types are acceptable alternatives
                    acceptable = {
                        'application/octet-stream': ['txt', 'md', 'json'],
                        'text/plain': ['txt', 'md', 'csv', 'json', 'xml']
                    }
                    if detected_mime not in acceptable or ext not in acceptable[detected_mime]:
                        return False, f"MIME type mismatch: {detected_mime} vs .{ext}", detected_mime
                
                return True, "", detected_mime
            except Exception as e:
                logger.warning(f"MIME validation failed: {e}")
        
        # Fallback: trust extension but warn
        guessed_mime, _ = mimetypes.guess_type(filename)
        return True, "", guessed_mime or "application/octet-stream"
    
    def scan_for_malware(self, file_path: Path) -> Tuple[bool, str]:
        """
        Basic malware scanning (placeholder for integration with ClamAV, etc.)
        """
        # Check for executable signatures
        dangerous_sigs = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'#!',  # Shebang script
            b'%PDF-1.',  # PDF (check for embedded JS)
        ]
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                
                # Check for double extensions (e.g., .jpg.exe)
                if file_path.name.count('.') > 2:
                    return False, "Suspicious filename: multiple extensions"
                
                # Check for executable content disguised as document
                exe_sigs = [b'MZ', b'\x7fELF', b'#!', b'<?php', b'<script']
                if any(sig in header for sig in exe_sigs):
                    # Check if it's actually a script in a code file
                    ext = file_path.suffix.lower()
                    if ext not in ['.py', '.js', '.sh', '.ps1', '.bat', '.cmd']:
                        return False, "Executable content detected in non-code file"
                
                # PDF JavaScript check
                if file_path.suffix.lower() == '.pdf':
                    content = f.read()
                    if b'/JavaScript' in content or b'/JS' in content:
                        return False, "PDF contains JavaScript (potential risk)"
                
                return True, "Clean"
                
        except Exception as e:
            logger.error(f"Malware scan failed: {e}")
            return False, f"Scan error: {e}"
    
    def upload_document(self, filename: str, content: Union[bytes, str], 
                       user_id: str = "default",
                       tags: List[str] = None, 
                       metadata: Dict = None, 
                       chat_id: str = None,
                       skip_processing: bool = False) -> Dict:
        """
        Upload and process any document type with full AI capabilities
        """
        logger.info(f"Uploading: {filename} for user {user_id}, chat {chat_id}")
        
        try:
            # Generate document ID
            doc_id = hashlib.md5(f"{filename}{user_id}{time.time()}".encode()).hexdigest()[:16]
            
            # Check for existing document
            existing = self.get_document_by_filename(filename, user_id)
            is_update = existing is not None
            if is_update:
                doc_id = existing.id
            
            # Determine file type
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            file_category = self.SUPPORTED_TYPES.get(ext, 'unknown')
            
            # MIME type detection
            mime_type = "application/octet-stream"
            if isinstance(content, bytes):
                if MAGIC_AVAILABLE:
                    try:
                        mime = magic.Magic(mime=True)
                        mime_type = mime.from_buffer(content[:8192])
                    except:
                        pass
                else:
                    mime_type, _ = mimetypes.guess_type(filename)
                    mime_type = mime_type or "application/octet-stream"
            
            file_size = len(content) if isinstance(content, bytes) else len(content.encode('utf-8'))
            
            # Process based on file category
            extraction_result = self._extract_content(content, file_category, ext, filename)
            text_content = extraction_result.get('text', '')
            ocr_text = extraction_result.get('ocr_text', '')
            extraction_method = extraction_result.get('method', 'unknown')
            
            # Generate thumbnail for images
            thumbnail_path = None
            if file_category == 'image' and PIL_AVAILABLE and isinstance(content, bytes):
                thumbnail_path = self._generate_thumbnail(content, doc_id)
            
            # Create chunks for RAG
            chunks = self._create_chunks(text_content + " " + ocr_text)
            
            # Generate initial summary
            summary = ""
            if text_content or ocr_text:
                summary_result = self.ai_processor.summarize(text_content + " " + ocr_text, 
                                                           max_length=200)
                if summary_result['success']:
                    summary = summary_result['summary']
            
            # Prepare metadata
            full_metadata = metadata or {}
            full_metadata.update({
                'extraction_method': extraction_method,
                'file_category': file_category,
                'original_size': file_size,
                'has_ocr': bool(ocr_text),
                'processing_version': '7.0'
            })
            if thumbnail_path:
                full_metadata['thumbnail'] = thumbnail_path
            
            # Save file to disk
            file_path = self.docs_dir / f"{doc_id}_{secure_filename(filename)}"
            if isinstance(content, bytes):
                with open(file_path, 'wb') as f:
                    f.write(content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Malware scan
            is_safe, scan_msg = self.scan_for_malware(file_path)
            if not is_safe:
                file_path.unlink()
                return {"success": False, "error": f"Security scan failed: {scan_msg}"}
            
            # Database operations
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if is_update:
                    # Archive current version
                    cursor.execute("""
                        INSERT INTO doc_history (id, doc_id, version, content, change_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (f"{doc_id}_v{existing.version}", doc_id, existing.version, 
                          existing.content, 'update'))
                    
                    # Update document
                    cursor.execute("""
                        UPDATE documents SET
                            content = ?, ocr_text = ?, summary = ?, updated_at = ?,
                            tags = ?, metadata = ?, version = version + 1,
                            file_size = ?, mime_type = ?, chat_id = ?,
                            extraction_method = ?, thumbnail_path = ?,
                            processing_status = ?
                        WHERE id = ?
                    """, (text_content, ocr_text, summary, now,
                          json.dumps(tags or []), json.dumps(full_metadata),
                          file_size, mime_type, chat_id,
                          extraction_method, thumbnail_path,
                          'pending' if not skip_processing else 'completed',
                          doc_id))
                    
                    # Clear old chunks
                    cursor.execute("DELETE FROM doc_chunks WHERE doc_id = ?", (doc_id,))
                    cursor.execute("DELETE FROM documents_fts WHERE doc_id = ?", (doc_id,))
                else:
                    # Insert new document
                    cursor.execute("""
                        INSERT INTO documents (
                            id, filename, title, content, ocr_text, doc_type,
                            file_category, uploaded_at, updated_at, user_id,
                            summary, tags, metadata, file_size, mime_type,
                            version, chat_id, shared, is_malicious,
                            processing_status, extraction_method, thumbnail_path
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (doc_id, filename, filename, text_content, ocr_text, ext,
                          file_category, now, now, user_id,
                          summary, json.dumps(tags or []), json.dumps(full_metadata),
                          file_size, mime_type, 1, chat_id, 0, 0,
                          'pending' if not skip_processing else 'completed',
                          extraction_method, thumbnail_path))
                
                # Insert chunks
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    keywords = self._extract_keywords(chunk.content)
                    cursor.execute("""
                        INSERT INTO doc_chunks (id, doc_id, chunk_index, content, keywords)
                        VALUES (?, ?, ?, ?, ?)
                    """, (chunk_id, doc_id, i, chunk.content, json.dumps(keywords)))
                    
                    # Update FTS index
                    cursor.execute("""
                        INSERT INTO documents_fts (content, ocr_text, doc_id)
                        VALUES (?, ?, ?)
                    """, (chunk.content, ocr_text[:1000] if i == 0 else "", doc_id))
                
                conn.commit()
            
            # Queue for async AI processing
            if not skip_processing:
                self.processing_queue.append((doc_id, user_id))
            
            result = {
                "success": True,
                "action": "updated" if is_update else "created",
                "document": {
                    "id": doc_id,
                    "filename": filename,
                    "title": filename,
                    "summary": summary,
                    "chunks": len(chunks),
                    "version": existing.version + 1 if is_update else 1,
                    "chat_id": chat_id,
                    "file_type": ext,
                    "file_category": file_category,
                    "file_size": file_size,
                    "mime_type": mime_type,
                    "extraction_method": extraction_method,
                    "has_ocr": bool(ocr_text),
                    "thumbnail": thumbnail_path,
                    "processing_status": "pending" if not skip_processing else "completed"
                }
            }
            
            if chat_id:
                result["chat_formatted"] = self.format_document_for_chat(doc_id, user_id)
            
            logger.info(f"Upload successful: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    
    def _extract_content(self, content: Union[bytes, str], file_category: str, 
                        ext: str, filename: str) -> Dict[str, str]:
        """
        Extract text content from various file types
        """
        result = {'text': '', 'ocr_text': '', 'method': 'unknown'}
        
        if isinstance(content, str):
            result['text'] = content
            result['method'] = 'text_direct'
            return result
        
        # Binary content processing
        if file_category == 'ooxml':
            result['text'] = self._extract_ooxml(content, ext)
            result['method'] = 'ooxml_native'
            
        elif ext == 'pdf':
            result['text'] = self._extract_pdf(content)
            result['method'] = 'pdf_extract'
            
            # If PDF has no text, try OCR
            if len(result['text'].strip()) < 100:
                ocr_result = self.ocr_processor.process_pdf_with_ocr(content)
                if ocr_result['success']:
                    result['ocr_text'] = ocr_result['text']
                    result['method'] = 'pdf_ocr'
                    
        elif file_category == 'image':
            ocr_result = self.ocr_processor.process_image(content)
            if ocr_result['success']:
                result['ocr_text'] = ocr_result['text']
                result['method'] = 'ocr'
                result['ocr_confidence'] = ocr_result.get('confidence', 0)
                
        elif file_category == 'open_document':
            result['text'] = self._extract_opendocument(content, ext)
            result['method'] = 'opendoc'
            
        elif file_category in ['text', 'code', 'markup', 'data']:
            # Try to decode as text
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    result['text'] = content.decode(encoding)
                    result['method'] = f'text_{encoding}'
                    break
                except:
                    continue
            if not result['text']:
                result['text'] = content.decode('utf-8', errors='ignore')
                
        elif file_category == 'rich_text':
            result['text'] = self._extract_rtf(content)
            result['method'] = 'rtf'
            
        elif file_category == 'ebook':
            result['text'] = self._extract_ebook(content, ext)
            result['method'] = 'ebook'
            
        elif file_category == 'archive':
            result['text'] = self._extract_archive_listing(content, ext, filename)
            result['method'] = 'archive_listing'
            
        elif file_category in ['audio', 'video']:
            result['text'] = self._extract_media_metadata(content, ext, filename)
            result['method'] = 'media_metadata'
            
        else:
            # Unknown binary - try to extract any text
            result['text'] = self._extract_text_from_binary(content)
            result['method'] = 'binary_heuristic'
        
        # Clean extracted text
        result['text'] = self._clean_text(result['text'])
        result['ocr_text'] = self._clean_text(result['ocr_text'])
        
        return result
    
    def _extract_ooxml(self, content: bytes, doc_type: str) -> str:
        """Extract text from Office Open XML files"""
        import zipfile
        import xml.etree.ElementTree as ET
        
        text_parts = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                if doc_type in ['docx', 'docm', 'dotx']:
                    # Word document
                    xml_file = 'word/document.xml'
                    if xml_file in z.namelist():
                        with z.open(xml_file) as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            # Extract all text nodes
                            for elem in root.iter():
                                if elem.text and elem.text.strip():
                                    text_parts.append(elem.text.strip())
                                    
                elif doc_type in ['xlsx', 'xlsm', 'xlsb']:
                    # Excel spreadsheet
                    if 'xl/sharedStrings.xml' in z.namelist():
                        with z.open('xl/sharedStrings.xml') as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                            for si in root.findall('.//ns:si', ns):
                                t = si.find('.//ns:t', ns)
                                if t is not None and t.text:
                                    text_parts.append(t.text)
                    # Also try to get sheet names
                    if 'xl/workbook.xml' in z.namelist():
                        with z.open('xl/workbook.xml') as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                            for sheet in root.findall('.//ns:sheet', ns):
                                name = sheet.get('name')
                                if name:
                                    text_parts.append(f"[Sheet: {name}]")
                                    
                elif doc_type in ['pptx', 'pptm', 'ppsx']:
                    # PowerPoint
                    for item in z.namelist():
                        if item.startswith('ppt/slides/slide') and item.endswith('.xml'):
                            with z.open(item) as f:
                                tree = ET.parse(f)
                                root = tree.getroot()
                                for elem in root.iter():
                                    if elem.text and elem.text.strip():
                                        text_parts.append(elem.text.strip())
                                        
        except Exception as e:
            logger.error(f"OOXML extraction failed: {e}")
            
        return '\n'.join(text_parts)
    
    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        # Try pdfplumber first
        if PDFPLUMBER_AVAILABLE:
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n\n'
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}")
        
        # Fallback to PyPDF2
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text += page.extract_text() + '\n\n'
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
            
        return text
    
    def _extract_opendocument(self, content: bytes, ext: str) -> str:
        """Extract from OpenDocument formats (ODT, ODS, ODP)"""
        import zipfile
        
        text_parts = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                if 'content.xml' in z.namelist():
                    with z.open('content.xml') as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        # Extract text from all elements
                        for elem in root.iter():
                            if elem.text and elem.text.strip():
                                text_parts.append(elem.text.strip())
        except Exception as e:
            logger.error(f"OpenDocument extraction failed: {e}")
            
        return '\n'.join(text_parts)
    
    def _extract_rtf(self, content: bytes) -> str:
        """Extract text from RTF"""
        try:
            # Simple RTF text extraction
            text = content.decode('latin-1', errors='ignore')
            # Remove RTF control words
            text = re.sub(r'\\[a-z]+(?:-?\d+)? ?', '', text)
            text = re.sub(r'[{}]', '', text)
            text = re.sub(r'\\\'[0-9a-fA-F]{2}', '', text)  # Hex escapes
            return text
        except Exception as e:
            logger.error(f"RTF extraction failed: {e}")
            return ""
    
    def _extract_ebook(self, content: bytes, ext: str) -> str:
        """Extract from EPUB/MOBI ebooks"""
        if ext == 'epub':
            return self._extract_epub(content)
        return "[Ebook extraction not implemented for this format]"
    
    def _extract_epub(self, content: bytes) -> str:
        """Extract text from EPUB"""
        import zipfile
        
        text_parts = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                # Find HTML content files
                html_files = [f for f in z.namelist() if f.endswith(('.html', '.xhtml', '.htm'))]
                for html_file in sorted(html_files)[:50]:  # Limit to first 50 chapters
                    with z.open(html_file) as f:
                        html = f.read().decode('utf-8', errors='ignore')
                        # Simple HTML tag stripping
                        text = re.sub(r'<[^>]+>', ' ', html)
                        text = re.sub(r'\s+', ' ', text)
                        text_parts.append(text.strip())
        except Exception as e:
            logger.error(f"EPUB extraction failed: {e}")
            
        return '\n\n'.join(text_parts)
    
    def _extract_archive_listing(self, content: bytes, ext: str, filename: str) -> str:
        """List contents of archive files"""
        try:
            if ext == 'zip':
                import zipfile
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    files = z.namelist()
                    return f"Archive: {filename}\nContains {len(files)} items:\n" + \
                           '\n'.join(f"  - {f}" for f in files[:100])
        except Exception as e:
            return f"[Archive listing failed: {e}]"
        return "[Archive contents]"
    
    def _extract_media_metadata(self, content: bytes, ext: str, filename: str) -> str:
        """Extract metadata from audio/video files"""
        # This would integrate with mutagen or similar library
        return f"[Media file: {filename}]\nType: {ext.upper()}\nSize: {len(content)} bytes"
    
    def _extract_text_from_binary(self, content: bytes) -> str:
        """Heuristic text extraction from unknown binary"""
        # Look for printable ASCII sequences
        text_parts = []
        current_seq = []
        
        for byte in content:
            if 32 <= byte <= 126 or byte in (9, 10, 13):  # Printable ASCII + whitespace
                current_seq.append(chr(byte))
            else:
                if len(current_seq) >= 4:  # Minimum sequence length
                    text_parts.append(''.join(current_seq))
                current_seq = []
        
        if len(current_seq) >= 4:
            text_parts.append(''.join(current_seq))
            
        return ' '.join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    def _create_chunks(self, text: str) -> List[DocumentChunk]:
        """Create intelligent chunks for RAG"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # Try to break at sentence boundary
            if end < text_len:
                # Look for sentence end within overlap range
                search_start = max(start + self.chunk_size - self.chunk_overlap, start)
                sentence_end = text.rfind('. ', search_start, end)
                if sentence_end > search_start:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                keywords = self._extract_keywords(chunk_text)
                chunks.append(DocumentChunk(
                    index=len(chunks),
                    content=chunk_text,
                    keywords=keywords
                ))
            
            start = end - self.chunk_overlap if end < text_len else text_len
        
        return chunks
    
    def _extract_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """Extract important keywords from text"""
        if not text:
            return []
        
        # Find words
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        
        # Common stop words
        stop_words = {
            'about', 'above', 'after', 'again', 'against', 'all', 'also', 'am', 'an', 
            'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 
            'below', 'between', 'both', 'but', 'by', 'can', 'did', 'do', 'does', 'doing', 
            'don', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 
            'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 
            'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 
            'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 
            'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 
            'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 
            'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 
            'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 
            'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 
            'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 
            'would', 'you', 'your', 'yours', 'yourself', 'yourselves'
        }
        
        # Filter and count
        filtered = [w for w in words if w not in stop_words and not w.isdigit()]
        word_freq = Counter(filtered)
        
        # Return top keywords
        return [word for word, count in word_freq.most_common(max_keywords)]
    
    def _generate_thumbnail(self, image_bytes: bytes, doc_id: str) -> Optional[str]:
        """Generate thumbnail for image documents"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Save
            thumb_filename = f"thumb_{doc_id}.jpg"
            thumb_path = self.thumbnails_dir / thumb_filename
            img.save(thumb_path, "JPEG", quality=85)
            
            return str(thumb_path)
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None
    
    # ==================== PUBLIC API METHODS ====================
    
    def get_document(self, doc_id: str, user_id: str = None) -> Optional[Document]:
        """Retrieve document by ID with optional user filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM documents WHERE id = ?"
                params = [doc_id]
                
                if user_id:
                    query += " AND (user_id = ? OR shared = 1)"
                    params.append(user_id)
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Load chunks
                cursor.execute("""
                    SELECT * FROM doc_chunks WHERE doc_id = ? ORDER BY chunk_index
                """, (doc_id,))
                chunk_rows = cursor.fetchall()
                
                chunks = []
                for cr in chunk_rows:
                    chunks.append(DocumentChunk(
                        index=cr['chunk_index'],
                        content=cr['content'],
                        keywords=json.loads(cr['keywords']) if cr['keywords'] else [],
                        page_number=cr['page_number'],
                        bounding_box=json.loads(cr['bounding_box']) if cr['bounding_box'] else None
                    ))
                
                return Document(
                    id=row['id'],
                    filename=row['filename'],
                    title=row['title'],
                    content=row['content'],
                    doc_type=row['doc_type'],
                    uploaded_at=row['uploaded_at'],
                    updated_at=row['updated_at'],
                    user_id=row['user_id'],
                    summary=row['summary'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    chunks=chunks,
                    file_size=row['file_size'],
                    mime_type=row['mime_type'],
                    version=row['version'],
                    chat_id=row['chat_id'],
                    ocr_text=row['ocr_text'],
                    entities=json.loads(row['entities']) if row['entities'] else {},
                    sentiment=json.loads(row['sentiment']) if row['sentiment'] else None,
                    language=row['language'],
                    shared=bool(row['shared']),
                    is_malicious=bool(row['is_malicious']),
                    processing_status=row['processing_status']
                )
                
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return None                                                              
    # ==================== PUBLIC API METHODS (CONTINUED) ====================
    
    def get_document_by_filename(self, filename: str, user_id: str = None) -> Optional[Document]:
        """Find document by filename"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT id FROM documents WHERE filename = ?"
                params = [filename]
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if row:
                    return self.get_document(row['id'], user_id)
        except Exception as e:
            logger.error(f"Error finding document by filename: {e}")
        return None
    
    def list_documents(self, limit: int = 100, user_id: str = None, 
                      include_shared: bool = False, chat_id: str = None,
                      doc_type: str = None, search_query: str = None) -> List[Dict]:
        """
        List documents with filtering and search capabilities
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT id, filename, title, doc_type, file_category,
                           uploaded_at, updated_at, summary, tags, metadata,
                           file_size, mime_type, version, chat_id, 
                           processing_status, language, shared
                    FROM documents 
                    WHERE 1=1
                """
                params = []
                
                if user_id:
                    if include_shared:
                        query += " AND (user_id = ? OR shared = 1)"
                    else:
                        query += " AND user_id = ?"
                    params.append(user_id)
                
                if chat_id:
                    query += " AND chat_id = ?"
                    params.append(chat_id)
                
                if doc_type:
                    query += " AND doc_type = ?"
                    params.append(doc_type)
                
                if search_query:
                    # Use FTS for text search
                    cursor.execute("""
                        SELECT doc_id FROM documents_fts 
                        WHERE documents_fts MATCH ?
                    """, (search_query,))
                    matching_ids = [r[0] for r in cursor.fetchall()]
                    if matching_ids:
                        placeholders = ','.join('?' * len(matching_ids))
                        query += f" AND id IN ({placeholders})"
                        params.extend(matching_ids)
                    else:
                        # Fallback to LIKE search on filename
                        query += " AND filename LIKE ?"
                        params.append(f"%{search_query}%")
                
                query += " ORDER BY updated_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                documents = []
                for row in rows:
                    doc_dict = {
                        "id": row['id'],
                        "filename": row['filename'],
                        "title": row['title'],
                        "doc_type": row['doc_type'],
                        "file_category": row['file_category'],
                        "uploaded_at": row['uploaded_at'],
                        "updated_at": row['updated_at'],
                        "summary": row['summary'][:200] + "..." if row['summary'] and len(row['summary']) > 200 else row['summary'],
                        "tags": json.loads(row['tags']) if row['tags'] else [],
                        "file_size": row['file_size'],
                        "mime_type": row['mime_type'],
                        "version": row['version'],
                        "chat_id": row['chat_id'],
                        "processing_status": row['processing_status'],
                        "language": row['language'],
                        "shared": bool(row['shared']),
                        "metadata": {k: v for k, v in json.loads(row['metadata']).items() 
                                   if k in ['thumbnail', 'has_ocr', 'extraction_method', 'file_category']}
                    }
                    documents.append(doc_dict)
                
                return documents
                
        except Exception as e:
            logger.error(f"List documents error: {e}")
            return []
    
    def get_recent_document_by_chat(self, chat_id: str, user_id: str = None) -> Optional[Document]:
        """Get the most recent document associated with a chat"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = """
                    SELECT id FROM documents
                    WHERE chat_id = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """
                params = [chat_id]
                if user_id:
                    query = query.replace("WHERE", "WHERE user_id = ? AND")
                    params.insert(0, user_id)
                cursor.execute(query, params)
                row = cursor.fetchone()
                if row:
                    return self.get_document(row['id'], user_id)
                return None
        except Exception as e:
            logger.error(f"Error getting recent document by chat: {e}")
            return None

    def delete_document(self, doc_id: str, user_id: str = None) -> bool:
        """Delete document with authorization check"""
        try:
            # Verify ownership
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return False
            
            # Delete file
            file_path = self.docs_dir / f"{doc_id}_{secure_filename(doc.filename)}"
            if file_path.exists():
                file_path.unlink()
            
            # Delete thumbnail if exists
            if doc.metadata.get('thumbnail'):
                thumb_path = Path(doc.metadata['thumbnail'])
                if thumb_path.exists():
                    thumb_path.unlink()
            
            # Delete from database (cascades to chunks, history)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Delete document error: {e}")
            return False
    
    # ==================== AI-POWERED DOCUMENT OPERATIONS ====================
    
    def summarize_document(self, doc_id: str, user_id: str = None, 
                          style: str = "neutral", max_length: int = 500) -> Dict:
        """
        Generate document summary with multiple styles
        
        Styles: neutral, executive, bullet_points, academic, simplified
        """
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return {"success": False, "error": "Document not found"}
            
            full_text = doc.content + " " + doc.ocr_text
            if not full_text.strip():
                return {"success": False, "error": "Document has no extractable text"}
            
            result = self.ai_processor.summarize(full_text, max_length=max_length, style=style)
            
            # Cache summary if successful
            if result['success'] and style == "neutral":
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE documents SET summary = ? WHERE id = ?
                    """, (result['summary'], doc_id))
                    conn.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {"success": False, "error": str(e)}
    
    def ask_document(self, doc_id: str, question: str, user_id: str = None,
                    use_cache: bool = True) -> Dict:
        """
        Ask questions about document content (RAG-based Q&A)
        """
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return {"success": False, "error": "Document not found"}
            
            # Check cache
            if use_cache:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT answer, confidence FROM doc_qa_cache 
                        WHERE doc_id = ? AND question = ?
                        AND created_at > datetime('now', '-7 days')
                    """, (doc_id, question))
                    cached = cursor.fetchone()
                    if cached:
                        return {
                            "success": True,
                            "answer": cached[0],
                            "confidence": cached[1],
                            "source": "cache"
                        }
            
            # Get relevant chunks
            relevant_chunks = self._get_relevant_chunks(doc_id, question, top_k=3)
            context = "\n\n".join([c.content for c in relevant_chunks])
            
            # Add OCR text if relevant
            if doc.ocr_text and any(kw in doc.ocr_text.lower() for kw in question.lower().split()):
                context += "\n\n[OCR Content]: " + doc.ocr_text[:1000]
            
            # Generate answer
            result = self.ai_processor.answer_question(context, question)
            
            # Cache result
            if result['success'] and use_cache:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cache_id = hashlib.md5(f"{doc_id}{question}{time.time()}".encode()).hexdigest()[:16]
                    cursor.execute("""
                        INSERT OR REPLACE INTO doc_qa_cache (id, doc_id, question, answer, confidence)
                        VALUES (?, ?, ?, ?, ?)
                    """, (cache_id, doc_id, question, result['answer'], result.get('confidence', 0)))
                    conn.commit()
            
            # Add source information
            result['sources'] = [{
                "chunk_index": c.index,
                "preview": c.content[:200] + "..."
            } for c in relevant_chunks]
            
            return result
            
        except Exception as e:
            logger.error(f"Q&A error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_relevant_chunks(self, doc_id: str, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """Retrieve most relevant chunks for a query using keyword matching"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all chunks for document
                cursor.execute("""
                    SELECT chunk_index, content, keywords FROM doc_chunks 
                    WHERE doc_id = ? ORDER BY chunk_index
                """, (doc_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # Score chunks by keyword overlap
                query_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', query.lower()))
                scored_chunks = []
                
                for row in rows:
                    chunk_keywords = set(json.loads(row[2])) if row[2] else set()
                    overlap = len(query_keywords & chunk_keywords)
                    scored_chunks.append((overlap, row[0], row[1]))
                
                # Sort by score and return top_k
                scored_chunks.sort(reverse=True)
                top_chunks = scored_chunks[:top_k]
                
                return [DocumentChunk(index=idx, content=content) 
                       for _, idx, content in top_chunks]
                
        except Exception as e:
            logger.error(f"Chunk retrieval error: {e}")
            return []
    
    def compare_documents(self, doc_id_1: str, doc_id_2: str, 
                         user_id: str = None) -> Dict:
        """
        Compare two documents and identify similarities/differences
        """
        try:
            doc1 = self.get_document(doc_id_1, user_id)
            doc2 = self.get_document(doc_id_2, user_id)
            
            if not doc1 or not doc2:
                return {"success": False, "error": "One or both documents not found"}
            
            # Check cache
            cache_key = tuple(sorted([doc_id_1, doc_id_2]))
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT similarity_score, comparison_data FROM doc_comparisons
                    WHERE (doc_id_1 = ? AND doc_id_2 = ?) OR (doc_id_1 = ? AND doc_id_2 = ?)
                    AND created_at > datetime('now', '-1 day')
                """, (doc_id_1, doc_id_2, doc_id_2, doc_id_1))
                cached = cursor.fetchone()
                
                if cached:
                    return {
                        "success": True,
                        "similarity_score": cached[0],
                        **json.loads(cached[1]),
                        "source": "cache"
                    }
            
            # Perform comparison
            text1 = doc1.content + " " + doc1.ocr_text
            text2 = doc2.content + " " + doc2.ocr_text
            
            result = self.ai_processor.compare_documents(text1, text2)
            
            # Add document metadata
            result['doc1'] = {
                "id": doc1.id,
                "filename": doc1.filename,
                "title": doc1.title,
                "word_count": len(text1.split())
            }
            result['doc2'] = {
                "id": doc2.id,
                "filename": doc2.filename,
                "title": doc2.title,
                "word_count": len(text2.split())
            }
            
            # Cache result
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                comp_id = hashlib.md5(f"{doc_id_1}{doc_id_2}{time.time()}".encode()).hexdigest()[:16]
                cursor.execute("""
                    INSERT INTO doc_comparisons (id, doc_id_1, doc_id_2, similarity_score, comparison_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (comp_id, doc_id_1, doc_id_2, result['similarity_score'], 
                      json.dumps({k: v for k, v in result.items() if k not in ['doc1', 'doc2']})))
                conn.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Comparison error: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_entities(self, doc_id: str, user_id: str = None) -> Dict:
        """
        Extract named entities from document: people, organizations, locations, dates, etc.
        """
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return {"success": False, "error": "Document not found"}
            
            full_text = doc.content + " " + doc.ocr_text
            if not full_text.strip():
                return {"success": False, "error": "Document has no extractable text"}
            
            entities = self.ai_processor.extract_entities(full_text)
            
            # Update document with extracted entities
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE documents SET entities = ? WHERE id = ?
                """, (json.dumps(entities), doc_id))
                conn.commit()
            
            return {
                "success": True,
                "entities": entities,
                "total_entities": sum(len(v) for v in entities.values())
            }
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_sentiment(self, doc_id: str, user_id: str = None) -> Dict:
        """
        Analyze sentiment of document content
        """
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return {"success": False, "error": "Document not found"}
            
            full_text = doc.content + " " + doc.ocr_text
            if not full_text.strip():
                return {"success": False, "error": "Document has no extractable text"}
            
            result = self.ai_processor.analyze_sentiment(full_text[:5000])  # Limit for performance
            
            # Update document
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE documents SET sentiment = ? WHERE id = ?
                """, (json.dumps(result) if result['success'] else None, doc_id))
                conn.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    def translate_document(self, doc_id: str, target_language: str, 
                          user_id: str = None) -> Dict:
        """
        Translate document content to target language
        
        Supported languages: en, es, fr, de, it, pt, zh, ja, ko, ru, ar, hi
        """
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return {"success": False, "error": "Document not found"}
            
            # Language code mapping
            lang_names = {
                'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
                'it': 'Italian', 'pt': 'Portuguese', 'zh': 'Chinese', 'ja': 'Japanese',
                'ko': 'Korean', 'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi',
                'nl': 'Dutch', 'pl': 'Polish', 'tr': 'Turkish', 'vi': 'Vietnamese'
            }
            
            if target_language not in lang_names:
                return {
                    "success": False, 
                    "error": f"Unsupported language: {target_language}",
                    "supported_languages": list(lang_names.keys())
                }
            
            # Detect source language
            source_lang = doc.language or self.ai_processor.detect_language(doc.content)
            
            # Try to use deep-translator if available
            try:
                from deep_translator import GoogleTranslator
                
                translator = GoogleTranslator(source=source_lang, target=target_language)
                
                # Translate in chunks to avoid limits
                text_to_translate = doc.content[:5000]  # Start with first 5000 chars
                translated = translator.translate(text_to_translate)
                
                # Create translated document
                new_filename = f"{os.path.splitext(doc.filename)[0]}_{target_language}{os.path.splitext(doc.filename)[1]}"
                
                # Store as new document
                result = self.upload_document(
                    filename=new_filename,
                    content=translated,
                    user_id=user_id,
                    tags=doc.tags + [f"translated_{target_language}", "translation"],
                    metadata={
                        **doc.metadata,
                        "original_doc_id": doc_id,
                        "source_language": source_lang,
                        "target_language": target_language,
                        "translation_method": "google_translate"
                    }
                )
                
                if result['success']:
                    return {
                        "success": True,
                        "translated_doc_id": result['document']['id'],
                        "source_language": source_lang,
                        "target_language": target_language,
                        "preview": translated[:500],
                        "word_count": len(translated.split())
                    }
                
            except ImportError:
                logger.warning("deep_translator not available for translation")
            
            # Fallback: return error with instructions
            return {
                "success": False,
                "error": "Translation service not available. Install deep_translator: pip install deep_translator",
                "detected_source_language": source_lang
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {"success": False, "error": str(e)}
    
    def search_across_documents(self, query: str, user_id: str = None, 
                                limit: int = 10) -> List[Dict]:
        """
        Semantic search across all documents using FTS and keyword matching
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Use FTS5 for full-text search
                cursor.execute("""
                    SELECT d.id, d.filename, d.title, d.doc_type, d.user_id,
                           d.uploaded_at, d.summary, d.mime_type,
                           c.content as matched_content, c.chunk_index,
                           rank as relevance_score
                    FROM documents_fts fts
                    JOIN documents d ON fts.doc_id = d.id
                    JOIN doc_chunks c ON fts.doc_id = c.doc_id AND fts.rowid = c.rowid
                    WHERE documents_fts MATCH ?
                    AND (d.user_id = ? OR d.shared = 1)
                    ORDER BY rank
                    LIMIT ?
                """, (query, user_id or "", limit))
                
                rows = cursor.fetchall()
                
                results = []
                seen_docs = set()
                
                for row in rows:
                    doc_id = row['id']
                    if doc_id in seen_docs:
                        continue
                    seen_docs.add(doc_id)
                    
                    results.append({
                        "doc_id": doc_id,
                        "filename": row['filename'],
                        "title": row['title'],
                        "doc_type": row['doc_type'],
                        "summary": row['summary'][:200] if row['summary'] else "",
                        "matched_excerpt": row['matched_content'][:300] + "..." if len(row['matched_content']) > 300 else row['matched_content'],
                        "relevance_score": row['relevance_score'],
                        "uploaded_at": row['uploaded_at']
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Cross-document search error: {e}")
            return []
    
    # ==================== FORMATTING & EXPORT ====================
    
    def format_document_for_chat(self, doc_id: str, user_id: str = None) -> str:
        """Format document for display in chat interface"""
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return "❌ Document not found"
            
            size_str = self._format_file_size(doc.file_size)
            
            try:
                dt = datetime.fromisoformat(doc.uploaded_at)
                time_str = dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                time_str = doc.uploaded_at
            
            icon = self._get_file_icon(doc.doc_type)
            file_category = doc.metadata.get('file_category', 'file')
            
            # Build preview
            preview_html = ""
            if file_category == 'image' and doc.metadata.get('thumbnail'):
                thumb_path = Path(doc.metadata['thumbnail'])
                thumb_filename = thumb_path.name
                preview_html = f"\n![Image preview](/docs/thumbnails/{thumb_filename})\n\n"
            elif file_category == 'image':
                preview_html = "\n📷 **Image file** (preview not available)\n\n"
            elif doc.ocr_text:
                preview_html = f"\n<details>\n<summary>📝 OCR Text (click to expand)</summary>\n\n```\n{doc.ocr_text[:500]}{'...' if len(doc.ocr_text) > 500 else ''}\n```\n\n</details>\n\n"
            else:
                preview_html = f"\n<details>\n<summary>📄 Content Preview (click to expand)</summary>\n\n```\n{doc.content[:1000]}{'...' if len(doc.content) > 1000 else ''}\n```\n\n</details>\n\n"
            
            # Show entities if available
            entities_section = ""
            if doc.entities and any(doc.entities.values()):
                entities_section = "\n🔍 **Detected Entities:**\n"
                for entity_type, items in doc.entities.items():
                    if items:
                        entities_section += f"• **{entity_type.title()}**: {', '.join(items[:5])}\n"
            
            # Show sentiment if available
            sentiment_section = ""
            if doc.sentiment:
                emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(doc.sentiment.get('sentiment', 'neutral'), "😐")
                sentiment_section = f"\n{emoji} **Sentiment**: {doc.sentiment.get('sentiment', 'unknown')} (confidence: {doc.sentiment.get('confidence', 0):.2f})\n"
            
            return f"""{icon} **Document: {doc.title}**  

📊 **File Details:**  
• **Type:** {doc.doc_type.upper()} ({file_category})  
• **Size:** {size_str}  
• **Language:** {doc.language.upper() if doc.language else 'Unknown'}  
• **Uploaded:** {time_str}  
• **ID:** `{doc.id}`  
{sentiment_section}
📝 **Summary:**  
{doc.summary or 'No summary available'}  
{entities_section}
{preview_html}
💡 **What would you like to do with this document?**  
• Ask me to **summarize** it (executive, bullet points, academic, or simplified)  
• **Extract key entities** (people, organizations, dates, locations)  
• Ask **specific questions** about its content  
• **Analyze sentiment** or tone  
• **Translate** to another language  
• **Compare** with another document  
• Search for **specific information** within it"""
            
        except Exception as e:
            logger.error(f"Format document error: {e}")
            return f"❌ Error formatting document: {e}"
    
    def export_document(self, doc_id: str, format_type: str, user_id: str = None) -> Dict:
        """
        Export document to various formats: txt, md, json, html, docx, pdf
        """
        try:
            doc = self.get_document(doc_id, user_id)
            if not doc:
                return {"success": False, "error": "Document not found"}
            
            base_name = os.path.splitext(doc.filename)[0]
            export_path = self.exports_dir / f"{base_name}_export_{int(time.time())}"
            
            if format_type == 'txt':
                output_path = export_path.with_suffix('.txt')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {doc.title}\n")
                    f.write(f"Exported: {datetime.now().isoformat()}\n")
                    f.write("="*50 + "\n\n")
                    f.write(doc.content)
                    if doc.ocr_text:
                        f.write("\n\n[OCR TEXT]\n")
                        f.write(doc.ocr_text)
                
                return {
                    "success": True,
                    "format": "txt",
                    "path": str(output_path),
                    "url": f"/exports/{output_path.name}"
                }
            
            elif format_type == 'json':
                output_path = export_path.with_suffix('.json')
                export_data = {
                    "document": {
                        "id": doc.id,
                        "filename": doc.filename,
                        "title": doc.title,
                        "content": doc.content,
                        "ocr_text": doc.ocr_text,
                        "summary": doc.summary,
                        "entities": doc.entities,
                        "sentiment": doc.sentiment,
                        "metadata": doc.metadata,
                        "uploaded_at": doc.uploaded_at
                    },
                    "exported_at": datetime.now().isoformat()
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                
                return {
                    "success": True,
                    "format": "json",
                    "path": str(output_path),
                    "url": f"/exports/{output_path.name}"
                }
            
            elif format_type == 'md':
                output_path = export_path.with_suffix('.md')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {doc.title}\n\n")
                    f.write(f"**Type:** {doc.doc_type}  \n")
                    f.write(f"**Uploaded:** {doc.uploaded_at}  \n")
                    f.write(f"**Size:** {self._format_file_size(doc.file_size)}  \n\n")
                    if doc.summary:
                        f.write(f"## Summary\n\n{doc.summary}\n\n")
                    f.write("## Content\n\n")
                    f.write(doc.content)
                
                return {
                    "success": True,
                    "format": "md",
                    "path": str(output_path),
                    "url": f"/exports/{output_path.name}"
                }
            
            elif format_type == 'html':
                output_path = export_path.with_suffix('.html')
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{doc.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .metadata {{ color: #666; margin-bottom: 20px; }}
        .content {{ line-height: 1.6; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>{doc.title}</h1>
    <div class="metadata">
        <p><strong>Type:</strong> {doc.doc_type}</p>
        <p><strong>Uploaded:</strong> {doc.uploaded_at}</p>
        <p><strong>Size:</strong> {self._format_file_size(doc.file_size)}</p>
    </div>
    <div class="content">{doc.content.replace(chr(10), '<br>')}</div>
</body>
</html>"""
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                return {
                    "success": True,
                    "format": "html",
                    "path": str(output_path),
                    "url": f"/exports/{output_path.name}"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported export format: {format_type}",
                    "supported_formats": ["txt", "md", "json", "html"]
                }
                
        except Exception as e:
            logger.error(f"Export error: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/1024**2:.1f} MB"
        else:
            return f"{size_bytes/1024**3:.2f} GB"
    
    def _get_file_icon(self, doc_type: str) -> str:
        """Get emoji icon for file type"""
        icons = {
            'txt': '📄', 'md': '📝', 'py': '🐍', 'js': '📜',
            'java': '☕', 'cpp': '⚙️', 'c': '⚙️', 'cs': '🔷',
            'html': '🌐', 'htm': '🌐', 'css': '🎨',
            'json': '📋', 'xml': '📋', 'csv': '📊',
            'pdf': '📕', 'docx': '📘', 'doc': '📘',
            'pptx': '📊', 'ppt': '📊', 'xlsx': '📈', 'xls': '📈',
            'zip': '📦', 'rar': '📦', '7z': '📦',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️', 
            'bmp': '🖼️', 'webp': '🖼️', 'tiff': '🖼️',
            'mp3': '🎵', 'mp4': '🎬', 'wav': '🎵', 'avi': '🎬',
            'epub': '📚', 'mobi': '📚'
        }
        return icons.get(doc_type.lower(), '📎')
    
    def get_document_stats(self, user_id: str = None) -> Dict:
        """Get comprehensive document statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Base query
                base_where = "WHERE user_id = ?" if user_id else ""
                params = [user_id] if user_id else []
                
                # Total counts
                cursor.execute(f"""
                    SELECT COUNT(*), SUM(file_size), 
                           COUNT(DISTINCT doc_type),
                           COUNT(DISTINCT language)
                    FROM documents {base_where}
                """, params)
                total, total_size, type_count, lang_count = cursor.fetchone()
                
                # By file category
                cursor.execute(f"""
                    SELECT file_category, COUNT(*), SUM(file_size)
                    FROM documents {base_where}
                    GROUP BY file_category
                """, params)
                by_category = {
                    row[0]: {"count": row[1], "size": row[2]} 
                    for row in cursor.fetchall()
                }
                
                # Processing status
                cursor.execute(f"""
                    SELECT processing_status, COUNT(*)
                    FROM documents {base_where}
                    GROUP BY processing_status
                """, params)
                processing_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Recent uploads (last 7 days)
                cursor.execute(f"""
                    SELECT COUNT(*) FROM documents 
                    {base_where}
                    AND uploaded_at > datetime('now', '-7 days')
                """, params)
                recent_uploads = cursor.fetchone()[0]
                
                return {
                    "success": True,
                    "total_documents": total or 0,
                    "total_size": total_size or 0,
                    "total_size_formatted": self._format_file_size(total_size or 0),
                    "document_types": type_count or 0,
                    "languages": lang_count or 0,
                    "by_category": by_category,
                    "processing_status": processing_status,
                    "recent_uploads_7d": recent_uploads
                }
                
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"success": False, "error": str(e)}


# ==================== FLASK API ROUTES ====================

def register_documentation_routes(app, doc_manager: DocumentationManager):
    """Register all documentation routes with Flask app"""
    
    from flask import request, jsonify, send_from_directory
    from functools import wraps
    
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Add your authentication logic here
            return f(*args, **kwargs)
        return decorated
    
    @app.route('/api/documents', methods=['GET'])
    def api_list_documents():
        """List documents with filtering"""
        user_id = request.args.get('user_id')
        chat_id = request.args.get('chat_id')
        search = request.args.get('search')
        doc_type = request.args.get('type')
        limit = min(int(request.args.get('limit', 100)), 500)
        
        docs = doc_manager.list_documents(
            limit=limit,
            user_id=user_id,
            include_shared=request.args.get('include_shared') == 'true',
            chat_id=chat_id,
            doc_type=doc_type,
            search_query=search
        )
        return jsonify({"success": True, "documents": docs, "count": len(docs)})
    
    @app.route('/api/documents', methods=['POST'])
    def api_upload_document():
        """Upload new document"""
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No filename"}), 400
        
        # Validate file
        is_valid, error_msg, mime_type = doc_manager.validate_file(file)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400
        
        # Read content
        content = file.read()
        file.seek(0)
        
        # Get parameters
        user_id = request.form.get('user_id', 'default')
        chat_id = request.form.get('chat_id')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        
        result = doc_manager.upload_document(
            filename=file.filename,
            content=content,
            user_id=user_id,
            chat_id=chat_id,
            tags=tags,
            metadata={"upload_mime_type": mime_type}
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @app.route('/api/documents/<doc_id>', methods=['GET'])
    def api_get_document(doc_id):
        """Get single document"""
        user_id = request.args.get('user_id')
        doc = doc_manager.get_document(doc_id, user_id)
        
        if not doc:
            return jsonify({"success": False, "error": "Document not found"}), 404
        
        return jsonify({
            "success": True,
            "document": doc.to_dict()
        })
    
    @app.route('/api/documents/<doc_id>', methods=['DELETE'])
    def api_delete_document(doc_id):
        """Delete document"""
        user_id = request.args.get('user_id')
        
        if doc_manager.delete_document(doc_id, user_id):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Document not found or access denied"}), 404
    
    @app.route('/api/documents/<doc_id>/summarize', methods=['POST'])
    def api_summarize_document(doc_id):
        """Generate document summary"""
        user_id = request.args.get('user_id')
        data = request.get_json() or {}
        
        result = doc_manager.summarize_document(
            doc_id=doc_id,
            user_id=user_id,
            style=data.get('style', 'neutral'),
            max_length=data.get('max_length', 500)
        )
        
        return jsonify(result)
    
    @app.route('/api/documents/<doc_id>/ask', methods=['POST'])
    def api_ask_document(doc_id):
        """Ask question about document"""
        user_id = request.args.get('user_id')
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({"success": False, "error": "Question required"}), 400
        
        result = doc_manager.ask_document(
            doc_id=doc_id,
            question=data['question'],
            user_id=user_id,
            use_cache=data.get('use_cache', True)
        )
        
        return jsonify(result)
    
    @app.route('/api/documents/<doc_id>/entities', methods=['GET'])
    def api_extract_entities(doc_id):
        """Extract named entities"""
        user_id = request.args.get('user_id')
        result = doc_manager.extract_entities(doc_id, user_id)
        return jsonify(result)
    
    @app.route('/api/documents/<doc_id>/sentiment', methods=['GET'])
    def api_analyze_sentiment(doc_id):
        """Analyze document sentiment"""
        user_id = request.args.get('user_id')
        result = doc_manager.analyze_sentiment(doc_id, user_id)
        return jsonify(result)
    
    @app.route('/api/documents/<doc_id>/translate', methods=['POST'])
    def api_translate_document(doc_id):
        """Translate document"""
        user_id = request.args.get('user_id')
        data = request.get_json()
        
        if not data or 'target_language' not in data:
            return jsonify({
                "success": False, 
                "error": "target_language required",
                "supported_languages": ["en", "es", "fr", "de", "it", "pt", "zh", "ja"]
            }), 400
        
        result = doc_manager.translate_document(
            doc_id=doc_id,
            target_language=data['target_language'],
            user_id=user_id
        )
        
        return jsonify(result)
    
    @app.route('/api/documents/compare', methods=['POST'])
    def api_compare_documents():
        """Compare two documents"""
        data = request.get_json()
        if not data or 'doc_id_1' not in data or 'doc_id_2' not in data:
            return jsonify({"success": False, "error": "Two document IDs required"}), 400
        
        result = doc_manager.compare_documents(
            doc_id_1=data['doc_id_1'],
            doc_id_2=data['doc_id_2'],
            user_id=data.get('user_id')
        )
        
        return jsonify(result)
    
    @app.route('/api/documents/search', methods=['GET'])
    def api_search_documents():
        """Search across all documents"""
        user_id = request.args.get('user_id')
        query = request.args.get('q')
        
        if not query:
            return jsonify({"success": False, "error": "Query parameter 'q' required"}), 400
        
        results = doc_manager.search_across_documents(
            query=query,
            user_id=user_id,
            limit=min(int(request.args.get('limit', 10)), 50)
        )
        
        return jsonify({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        })
    
    @app.route('/api/documents/<doc_id>/export', methods=['POST'])
    def api_export_document(doc_id):
        """Export document to various formats"""
        user_id = request.args.get('user_id')
        data = request.get_json() or {}
        format_type = data.get('format', 'txt')
        
        result = doc_manager.export_document(doc_id, format_type, user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    @app.route('/api/documents/stats', methods=['GET'])
    def api_document_stats():
        """Get document statistics"""
        user_id = request.args.get('user_id')
        stats = doc_manager.get_document_stats(user_id)
        return jsonify(stats)
    
    @app.route('/exports/<path:filename>')
    def doc_serve_export(filename):
        """Serve exported files"""
        return send_from_directory(doc_manager.exports_dir, filename)
    
    @app.route('/docs/thumbnails/<path:filename>')
    def doc_serve_thumbnail(filename):
        """Serve thumbnail images"""
        return send_from_directory(doc_manager.thumbnails_dir, filename)
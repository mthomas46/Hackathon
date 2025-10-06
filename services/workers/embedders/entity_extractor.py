"""Entity Extractor Worker - Extract entities using NLP."""

import logging
from typing import Any, Dict, List, Optional, Set

from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseEmbedder, Document, WorkerResult

logger = logging.getLogger(__name__)


class EntityExtractor(BaseEmbedder):
    """Extract named entities from documents."""
    
    def __init__(self):
        super().__init__("entity_extractor")
        self.nlp = None
    
    def _load_spacy(self):
        """Lazy load spaCy model."""
        if self.nlp is None:
            try:
                import spacy
                # Try to load model, fallback to blank if not available
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except:
                    self.logger.warning("spaCy model not found, using blank model")
                    self.nlp = spacy.blank("en")
            except ImportError:
                self.logger.error("spaCy not installed")
                self.nlp = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def embed(self, documents: List[Document]) -> List[Document]:
        """
        Extract entities from documents.
        
        Extracts:
        - People (PERSON)
        - Organizations (ORG)
        - Products (PRODUCT)
        - Technologies (GPE, NORP)
        - Dates (DATE)
        - Concepts (custom extraction)
        """
        self._load_spacy()
        
        if self.nlp is None:
            self.logger.error("spaCy not available, skipping entity extraction")
            return documents
        
        enriched_docs = []
        
        for doc in documents:
            try:
                # Extract entities
                entities = await self._extract_entities(doc)
                
                doc.entities = entities
                doc.metadata["entities_extracted"] = True
                doc.metadata["entity_count"] = len(entities)
                
                enriched_docs.append(doc)
                
            except Exception as e:
                self.logger.error(f"Error extracting entities from {doc.doc_id}: {e}")
                enriched_docs.append(doc)
        
        return enriched_docs
    
    async def _extract_entities(self, doc: Document) -> List[Dict[str, Any]]:
        """Extract entities from a single document."""
        entities = []
        seen: Set[str] = set()
        
        # Combine title and content (limit for performance)
        text = f"{doc.title}\n\n{doc.content[:5000]}"
        
        # Process with spaCy
        spacy_doc = self.nlp(text)
        
        # Extract named entities
        for ent in spacy_doc.ents:
            entity_key = f"{ent.text.lower()}:{ent.label_}"
            
            if entity_key not in seen:
                seen.add(entity_key)
                
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "category": self._categorize_entity(ent.label_)
                })
        
        # Extract technical terms (simple heuristic)
        tech_terms = self._extract_technical_terms(doc)
        for term in tech_terms:
            entity_key = f"{term.lower()}:TECH"
            if entity_key not in seen:
                seen.add(entity_key)
                entities.append({
                    "text": term,
                    "type": "TECH",
                    "category": "technology"
                })
        
        return entities
    
    def _categorize_entity(self, label: str) -> str:
        """Categorize entity label into broader category."""
        categories = {
            "PERSON": "person",
            "ORG": "organization",
            "GPE": "location",
            "PRODUCT": "product",
            "WORK_OF_ART": "concept",
            "LAW": "concept",
            "LANGUAGE": "technology",
            "DATE": "temporal",
            "TIME": "temporal",
            "MONEY": "financial",
            "QUANTITY": "metric",
        }
        
        return categories.get(label, "other")
    
    def _extract_technical_terms(self, doc: Document) -> List[str]:
        """Extract technical terms using heuristics."""
        import re
        
        tech_patterns = [
            # Programming languages
            r'\b(python|javascript|typescript|java|go|rust|scala|kotlin|swift)\b',
            # Frameworks
            r'\b(react|vue|angular|django|flask|fastapi|spring|express)\b',
            # Databases
            r'\b(postgresql|mysql|mongodb|redis|cassandra|dynamodb|neo4j)\b',
            # Cloud/Infra
            r'\b(aws|azure|gcp|kubernetes|docker|terraform|ansible)\b',
            # Protocols
            r'\b(http|https|grpc|graphql|rest|api|websocket|mqtt)\b',
        ]
        
        content_lower = doc.content.lower()
        terms: Set[str] = set()
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            terms.update(matches)
        
        # Also check tags for tech terms
        tech_tags = [t for t in doc.tags if len(t) > 2]
        terms.update(tech_tags)
        
        return list(terms)[:20]  # Limit to 20 tech terms


# Celery task
@app.task(name="extract_entities", bind=True)
def extract_entities_task(
    self,
    documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Celery task for entity extraction."""
    import asyncio
    
    # Convert dicts back to Document objects
    from services.workers.shared.base_worker import Document
    
    doc_objects = []
    for d in documents:
        doc = Document(
            doc_id=d["doc_id"],
            source=d["source"],
            source_type=d["source_type"],
            title=d["title"],
            content=d["content"],
            raw_content=d.get("raw_content", ""),
            metadata=d.get("metadata", {}),
            tags=d.get("tags", []),
            tier=d.get("tier"),
            entities=d.get("entities", []),
        )
        doc_objects.append(doc)
    
    extractor = EntityExtractor()
    
    # Run async extraction
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(extractor.process({"documents": doc_objects}))
    
    return result.dict()


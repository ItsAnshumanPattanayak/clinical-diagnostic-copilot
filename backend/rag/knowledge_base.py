"""
Retrieval-Augmented Generation (RAG) Knowledge Base
===================================================
Simulates a vector database with medical literature.

In production, you'd use:
- Pinecone, Weaviate, or ChromaDB for vector storage
- OpenAI/Cohere embeddings for semantic search
- PubMed API for real medical literature

This mock implementation uses keyword matching for simplicity.
"""

from typing import List, Dict, Optional
import re


class MedicalKnowledgeBase:
    """
    In-memory medical knowledge base with keyword search.
    
    Simulates what a real vector database would provide:
    - Semantic search over medical literature
    - Contextual retrieval for agent reasoning
    - Citation tracking
    """
    
    def __init__(self):
        """Initialize with hardcoded medical literature snippets."""
        
        # Each document represents a medical study or clinical guideline
        # In production, this would be 1000s of documents in a vector DB
        self.documents = [
            {
                "id": "doc_001",
                "title": "Diabetic Retinopathy Screening Guidelines",
                "content": """Diabetic retinopathy is the leading cause of blindness in 
                working-age adults. Early detection through fundus imaging can reduce vision 
                loss by 95%. Screening recommendations: annual examination for Type 1 diabetes 
                patients (5 years post-diagnosis) and all Type 2 diabetes patients at diagnosis. 
                Key findings include microaneurysms, hemorrhages, and exudates. Treatment options 
                include laser photocoagulation and anti-VEGF injections.""",
                "keywords": ["diabetic", "retinopathy", "diabetes", "fundus", "screening", "vision"],
                "source": "American Academy of Ophthalmology (2021)",
                "relevance_score": 0.95
            },
            {
                "id": "doc_002",
                "title": "Glaucoma Detection via Optic Disc Assessment",
                "content": """Glaucoma is characterized by progressive optic nerve damage, 
                leading to irreversible vision loss. Primary open-angle glaucoma (POAG) is most 
                common. Key imaging biomarkers include increased cup-to-disc ratio (>0.6), 
                rim thinning, and retinal nerve fiber layer defects. Intraocular pressure 
                measurement and visual field testing are essential. Treatment focuses on 
                pressure reduction via medications or surgery.""",
                "keywords": ["glaucoma", "optic nerve", "pressure", "cup-to-disc", "vision loss"],
                "source": "Journal of Glaucoma (2020)",
                "relevance_score": 0.92
            },
            {
                "id": "doc_003",
                "title": "Age-Related Macular Degeneration (AMD) Pathophysiology",
                "content": """AMD affects central vision due to macula deterioration. Two forms: 
                dry AMD (geographic atrophy) and wet AMD (choroidal neovascularization). Risk 
                factors include age >60, smoking, and family history. OCT imaging shows drusen 
                deposits and retinal thickening. Anti-VEGF therapy (ranibizumab, aflibercept) 
                has revolutionized wet AMD treatment, preserving vision in 90% of cases.""",
                "keywords": ["macular degeneration", "AMD", "macula", "drusen", "VEGF", "aging"],
                "source": "Retina Journal (2022)",
                "relevance_score": 0.89
            },
            {
                "id": "doc_004",
                "title": "Cataract Surgery Outcomes and Indications",
                "content": """Cataracts cause progressive lens opacity, resulting in blurred 
                vision and glare. Most common in patients >65 years. Diagnosis via slit-lamp 
                examination. Surgical intervention (phacoemulsification with IOL implantation) 
                has 95% success rate. Indications for surgery: visual acuity <20/40 affecting 
                daily activities. Postoperative complications are rare with modern techniques.""",
                "keywords": ["cataract", "lens", "surgery", "opacity", "vision", "aging"],
                "source": "Ophthalmology Times (2021)",
                "relevance_score": 0.88
            },
            {
                "id": "doc_005",
                "title": "Normal Fundus Anatomy and Healthy Retina Characteristics",
                "content": """A healthy retina shows clear optic disc margins, pink neuroretinal 
                rim, cup-to-disc ratio <0.5, intact macula with foveal reflex, and uniform 
                vascular distribution. No hemorrhages, exudates, or cotton-wool spots should be 
                present. Regular screening helps establish baseline for future comparisons. 
                Healthy lifestyle factors include controlled blood pressure and glucose levels.""",
                "keywords": ["normal", "healthy", "retina", "fundus", "baseline", "screening"],
                "source": "Clinical Ophthalmology Reference (2020)",
                "relevance_score": 0.85
            },
            {
                "id": "doc_006",
                "title": "AI in Medical Imaging: Opportunities and Limitations",
                "content": """Deep learning models show promise in medical image analysis, 
                achieving expert-level performance in diabetic retinopathy and breast cancer 
                screening. However, limitations include: need for large annotated datasets, 
                black-box decision-making, and distribution shift in real-world deployment. 
                Clinical validation requires prospective trials. AI should augment, not replace, 
                physician judgment. FDA approval requires rigorous testing.""",
                "keywords": ["AI", "machine learning", "deep learning", "validation", "clinical"],
                "source": "Nature Medicine (2023)",
                "relevance_score": 0.90
            }
        ]
        
        print(f"✓ Knowledge base initialized with {len(self.documents)} medical documents")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant documents using keyword matching.
        
        In production, this would be:
        1. Embed query using sentence-transformers
        2. Perform cosine similarity search in vector DB
        3. Re-rank using cross-encoders
        
        Args:
            query: Search query (e.g., "diabetic retinopathy treatment")
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with scores
        """
        # Normalize query
        query_lower = query.lower()
        query_terms = re.findall(r'\w+', query_lower)
        
        # Score each document
        scored_docs = []
        for doc in self.documents:
            score = self._calculate_relevance(query_terms, doc)
            if score > 0:
                scored_docs.append({
                    **doc,
                    "search_score": score
                })
        
        # Sort by score and return top_k
        scored_docs.sort(key=lambda x: x['search_score'], reverse=True)
        return scored_docs[:top_k]
    
    def _calculate_relevance(self, query_terms: List[str], document: Dict) -> float:
        """
        Calculate relevance score using keyword overlap.
        
        Real implementation would use:
        - TF-IDF weighting
        - BM25 ranking
        - Dense vector similarity
        
        Args:
            query_terms: List of search terms
            document: Document dictionary
            
        Returns:
            Relevance score (0-1)
        """
        doc_text = (document['title'] + ' ' + document['content']).lower()
        keyword_text = ' '.join(document['keywords']).lower()
        
        # Count matching terms
        matches = 0
        for term in query_terms:
            if term in keyword_text:
                matches += 2  # Keywords weighted higher
            elif term in doc_text:
                matches += 1
        
        # Normalize by query length
        if len(query_terms) == 0:
            return 0.0
        
        base_score = matches / (len(query_terms) * 2)
        
        # Combine with document's inherent relevance score
        final_score = (base_score * 0.7) + (document['relevance_score'] * 0.3)
        
        return min(final_score, 1.0)
    
    def get_context_for_diagnosis(self, diagnosis: str) -> str:
        """
        Retrieve formatted context for a specific diagnosis.
        
        This is used by agents to get background information.
        
        Args:
            diagnosis: Medical condition name
            
        Returns:
            Formatted text context
        """
        results = self.search(diagnosis, top_k=2)
        
        if not results:
            return "No specific literature found for this condition."
        
        context = "Relevant Medical Literature:\n\n"
        for i, doc in enumerate(results, 1):
            context += f"{i}. {doc['title']}\n"
            context += f"   Source: {doc['source']}\n"
            context += f"   {doc['content'][:300]}...\n\n"
        
        return context


# Singleton instance
knowledge_base = MedicalKnowledgeBase()


def search_medical_literature(query: str, top_k: int = 3) -> List[Dict]:
    """
    Public API for medical literature search.
    
    Args:
        query: Search query
        top_k: Number of results
        
    Returns:
        List of relevant documents
    """
    return knowledge_base.search(query, top_k)
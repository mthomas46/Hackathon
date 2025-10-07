---
llm_metadata:
  document_type: reference
  content_focus: historical
  platform:
    primary: shared
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - python
  - rag
  - embeddings
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Reference document about historical aspects of the shared platform
  archive_reason: consolidated
  historical_value: medium
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# 🎯 **LLM PATTERN DECISION FRAMEWORK**

**Purpose:** Guide intelligent pattern selection based on problem characteristics  
**Date:** October 6, 2025  
**Version:** 1.0  

---

## 🔍 **CORE DECISION: RAG vs THOUGHT PATTERNS**

### **Two Fundamental Categories**

1. **RAG (Retrieval-Augmented Generation) Patterns**
   - Focus: Finding and using external information
   - Complexity: In retrieval and information location

2. **Thought Patterns**
   - Focus: Internal reasoning and logic
   - Complexity: In reasoning process itself

---

## 📊 **DECISION CRITERIA**

### **Factor 1: Data Source**

| Use RAG Patterns | Use Thought Patterns |
|------------------|----------------------|
| Answers must be grounded in specific, external, up-to-date information | General knowledge or logical reasoning tasks |
| Examples: Legal documents, proprietary knowledge, product manuals | Examples: Creative writing, complex problem-solving |
| **Pattern:** Advanced RAG, HyDE, CRAG, Parent Retriever | **Pattern:** CoT, ToT, GoT, SoT |

### **Factor 2: Problem Type**

| Use RAG Patterns | Use Thought Patterns |
|------------------|----------------------|
| Complexity lies in **retrieving** the correct information | Complexity lies in **reasoning** process itself |
| Information exists but must be found | Step-by-step logic, multi-stage planning needed |
| Then passed to LLM for summarization/synthesis | Evaluating multiple possibilities |
| **Pattern:** Advanced RAG, Parent Retriever | **Pattern:** ToT, GoT, Self-Consistency |

### **Factor 3: Primary Goal**

| Use RAG Patterns | Use Thought Patterns |
|------------------|----------------------|
| **Factual accuracy** is critical | **Logical consistency** is critical |
| **Transparency** (providing sources) | **Reliable reasoning** process |
| **Mitigating hallucinations** | Less linear, more thorough reasoning |
| **Pattern:** CRAG, Advanced RAG | **Pattern:** Self-Consistency, Constitutional AI |

### **Factor 4: Performance Needs**

| Use RAG Patterns | Use Thought Patterns |
|------------------|----------------------|
| LLM's internal knowledge is **insufficient** | LLM's **reasoning is weak** |
| Information **prone to becoming outdated** | Jumps to conclusions too quickly |
| Retrieval is a **necessary step** in pipeline | Makes logical errors even with good context |
| **Pattern:** CRAG, HyDE | **Pattern:** CoT, ToT, Self-Critique |

### **Factor 5: Key Metrics**

| Use RAG Patterns | Use Thought Patterns |
|------------------|----------------------|
| Retrieval metrics (precision/recall) | Reasoning benchmarks |
| Is the correct chunk retrieved? | Logical consistency |
| Hallucination rate | Answer quality |
| **Pattern:** Reranking, CRAG | **Pattern:** Self-Consistency, ToT |

---

## 🎯 **PATTERN SELECTION GUIDE**

### **RAG Patterns**

#### When to Use Each RAG Pattern

**1. Advanced RAG**
- **When:** Multi-source retrieval needed, comprehensive coverage
- **Best for:** Complex queries requiring multiple information sources
- **Combines:** Query decomposition + retrieval + reranking + fusion

**2. Hypothetical Document Embeddings (HyDE)**
- **When:** Query is ambiguous or conceptual
- **Best for:** Abstract questions, semantic search
- **Innovation:** Generate hypothetical answer first, use for retrieval

**3. Parent Document Retriever**
- **When:** Need broader context than retrieved chunk
- **Best for:** Nuanced questions requiring surrounding context
- **Innovation:** Retrieve small, return large (hierarchical)

**4. Corrective RAG (CRAG)**
- **When:** Retrieval quality is uncertain
- **Best for:** Critical applications requiring fallback
- **Innovation:** Evaluate retrieval, web search if insufficient

**5. Reranking**
- **When:** Initial retrieval needs refinement
- **Best for:** Large result sets needing prioritization
- **Innovation:** Multiple reranking strategies, cross-encoder

---

### **Thought Patterns**

#### When to Use Each Thought Pattern

**1. Chain-of-Thought (CoT)**
- **When:** Simple step-by-step reasoning needed
- **Best for:** Logical problems, math, explanations
- **Speed:** Fast (5-15s)

**2. Tree-of-Thought (ToT)**
- **When:** Multiple approaches should be explored
- **Best for:** Strategic decisions, complex planning
- **Speed:** Slow (30-60s), thorough

**3. Graph-of-Thought (GoT)**
- **When:** Non-linear, interconnected reasoning needed
- **Best for:** Complex systems, circular dependencies
- **Speed:** Slow (30-45s), comprehensive

**4. Self-Consistency**
- **When:** Accuracy through consensus is critical
- **Best for:** Math, verifiable answers
- **Speed:** Medium (10-20s), reliable

**5. Skeleton of Thoughts (SoT)**
- **When:** Structured breakdown with parallel elaboration
- **Best for:** Long-form content, complex explanations
- **Speed:** Medium (20-40s), parallel

**6. Rephrase and Respond (RaR)**
- **When:** Query clarity is the issue
- **Best for:** Ambiguous questions
- **Speed:** Fast (10-20s), clarifying

**7. Expert Persona**
- **When:** Domain expertise simulation needed
- **Best for:** Specialized domains (medical, legal, technical)
- **Speed:** Medium (15-30s), domain-focused

---

## 🔄 **HYBRID APPROACHES**

### **Best of Both Worlds**

Combine RAG + Thought patterns for maximum power!

#### **Hybrid Pattern Examples**

**1. RAG + CoT: Grounded Reasoning**
```
1. Retrieve relevant documents (RAG)
2. Apply step-by-step reasoning on retrieved content (CoT)
```
**Use Case:** "Based on our docs, explain why feature X works"

**2. HyDE + ToT: Conceptual Exploration**
```
1. Generate hypothetical documents (HyDE)
2. Explore multiple reasoning paths (ToT)
```
**Use Case:** Abstract problem-solving with information retrieval

**3. CRAG + Expert Persona: Verified Expertise**
```
1. Corrective retrieval with fallback (CRAG)
2. Apply expert reasoning (Expert Persona)
```
**Use Case:** Medical diagnosis, legal analysis

**4. Parent Retriever + SoT: Contextual Structure**
```
1. Retrieve with full context (Parent Retriever)
2. Generate skeleton and elaborate (SoT)
```
**Use Case:** Comprehensive documentation queries

**5. Advanced RAG + Self-Consistency: Robust Answers**
```
1. Multi-source retrieval (Advanced RAG)
2. Multiple reasoning paths + voting (Self-Consistency)
```
**Use Case:** Critical decisions requiring both grounding and reliability

---

## 📋 **DECISION FLOWCHART**

```
START: Analyze Query
    ↓
[Q1: Need External Info?]
    ↓
    YES → [Q2: Info Up-to-date?]
    │         ↓
    │         YES → Use RAG Pattern
    │         │       ↓
    │         │   [Q3: Retrieval Uncertain?]
    │         │       ↓
    │         │   YES → CRAG
    │         │   NO → Advanced RAG / HyDE
    │         │
    │         NO → Thought Pattern
    │                 ↓
    │             [Q4: Reasoning Complex?]
    │                 ↓
    │             YES → ToT / GoT
    │             NO → CoT
    │
    NO → [Q5: Domain Expertise?]
            ↓
        YES → Expert Persona
        NO → CoT / Self-Consistency

[Q6: Need Both?]
    ↓
    YES → Hybrid Approach
```

---

## 🎯 **REAL-WORLD EXAMPLES**

### **Example 1: Legal Question**
**Query:** "What are the implications of clause 7.3 in our contract?"

**Analysis:**
- Need external info: YES (contract document)
- Info up-to-date: YES (specific contract)
- Domain expertise: YES (legal)

**Pattern Selection:** `CRAG + Expert Persona`
1. Retrieve clause 7.3 with verification
2. Apply legal expert reasoning

---

### **Example 2: Strategic Planning**
**Query:** "What's the best approach to enter the European market?"

**Analysis:**
- Need external info: YES (market data)
- Reasoning complex: YES (multiple factors)

**Pattern Selection:** `Advanced RAG + ToT`
1. Retrieve market research, competitor analysis
2. Explore multiple strategic approaches
3. Evaluate and select best path

---

### **Example 3: Math Problem**
**Query:** "Solve this calculus problem: ..."

**Analysis:**
- Need external info: NO (pure reasoning)
- Reasoning type: Step-by-step
- Need reliability: YES

**Pattern Selection:** `Self-Consistency`
1. Multiple reasoning paths
2. Majority voting for correct answer

---

### **Example 4: Abstract Research**
**Query:** "What are emerging trends in quantum computing?"

**Analysis:**
- Need external info: YES (recent research)
- Query is conceptual: YES
- Need broad coverage: YES

**Pattern Selection:** `HyDE + Parent Retriever`
1. Generate hypothetical research summary
2. Use for semantic search
3. Return full research papers
4. Synthesize trends

---

## 🔍 **PATTERN SELECTOR ALGORITHM**

```python
def select_pattern(query, context, requirements):
    """
    Intelligent pattern selection based on query characteristics.
    """
    
    # Analyze query
    needs_external_info = requires_retrieval(query)
    reasoning_complexity = assess_complexity(query)
    domain = identify_domain(query)
    accuracy_critical = check_criticality(requirements)
    
    # Decision tree
    if needs_external_info:
        if query_is_ambiguous(query):
            pattern = "HyDE"
        elif retrieval_uncertain(context):
            pattern = "CRAG"
        elif needs_broad_context():
            pattern = "Parent Retriever"
        else:
            pattern = "Advanced RAG"
        
        # Add reasoning if complex
        if reasoning_complexity == "high":
            pattern = f"{pattern} + ToT"
        elif domain in ["medical", "legal", "technical"]:
            pattern = f"{pattern} + Expert Persona"
            
    else:  # Pure reasoning
        if reasoning_complexity == "simple":
            pattern = "CoT"
        elif reasoning_complexity == "strategic":
            pattern = "ToT"
        elif reasoning_complexity == "interconnected":
            pattern = "GoT"
        elif needs_structure():
            pattern = "SoT"
        
        if accuracy_critical:
            pattern = f"{pattern} + Self-Consistency"
    
    return pattern
```

---

## 📊 **PATTERN COMPARISON MATRIX**

| Pattern | Speed | Accuracy | External Info | Reasoning | Best For |
|---------|-------|----------|---------------|-----------|----------|
| **Advanced RAG** | Medium | High | ✅ Yes | Basic | Multi-source queries |
| **HyDE** | Medium | High | ✅ Yes | Basic | Abstract queries |
| **CRAG** | Medium | Very High | ✅ Yes | Basic | Critical retrieval |
| **Parent Retriever** | Medium | High | ✅ Yes | Basic | Context-rich queries |
| **CoT** | Fast | Medium | ❌ No | ✅ Step-by-step | Simple logic |
| **ToT** | Slow | High | ❌ No | ✅ Multi-path | Strategy |
| **GoT** | Slow | High | ❌ No | ✅ Graph | Complex systems |
| **Self-Consistency** | Medium | Very High | ❌ No | ✅ Voting | Math/facts |
| **SoT** | Medium | High | ❌ No | ✅ Structured | Long-form |
| **Expert Persona** | Medium | High | ❌ No | ✅ Domain | Specialized |

---

## 🎯 **SUMMARY**

### **Quick Decision Guide**

**Use RAG when:**
- ✅ Need specific external information
- ✅ Factual accuracy is critical
- ✅ Must cite sources
- ✅ Information changes over time

**Use Thought Patterns when:**
- ✅ Reasoning complexity is the challenge
- ✅ Logical consistency matters most
- ✅ General knowledge is sufficient
- ✅ Need creative or strategic thinking

**Use Hybrid when:**
- ✅ Both retrieval AND reasoning are complex
- ✅ Domain expertise + external info needed
- ✅ Critical decisions requiring both grounding and logic

---

**Framework Version:** 1.0  
**Last Updated:** October 6, 2025  
**Status:** ✅ Complete & Ready for Integration  

**Next Step:** Integrate into Adaptive Selection pattern for automatic pattern selection! 🎯


# 🧠 ECOSYSTEM MCP - FINE-TUNING FRAMEWORK GUIDE

**Version**: 0.1.0  
**Date**: October 2025  
**Purpose**: Document fine-tuning methodology for custom LLMs

---

## 📋 OVERVIEW

This guide documents **how to fine-tune LLMs** on the ingested documentation corpus. The Ecosystem MCP service is designed to support fine-tuning workflows, though **fine-tuning itself is not implemented in the MVP**.

### What This Service Provides

✅ **Data Collection**: Comprehensive document ingestion  
✅ **Data Organization**: Version-controlled, tagged, embedded  
✅ **Data Export**: Structured format for training  
✅ **Metadata Tracking**: Git history, relationships, topics  
✅ **Quality Metrics**: Word counts, complexity scores

### What This Guide Documents

📚 **Fine-Tuning Process**: Step-by-step methodology  
📚 **Data Preparation**: How to export and format data  
📚 **Model Selection**: Which models to fine-tune  
📚 **Evaluation**: How to measure improvements  
📚 **Deployment**: How to serve fine-tuned models

---

## 🎯 WHY FINE-TUNE?

### Use Cases

1. **Domain-Specific Knowledge**
   - Understand your exact architecture
   - Know your coding standards
   - Recognize your patterns

2. **Context Efficiency**
   - Reduce prompt tokens needed
   - Faster inference
   - Lower costs

3. **Consistency**
   - Predictable outputs
   - Aligned with your practices
   - Reduced hallucinations

### ROI Calculation

**Baseline** (GPT-4 with RAG):
- Cost: $0.03/1K input tokens
- Context: 8K tokens average
- Cost per query: ~$0.24

**Fine-Tuned** (GPT-3.5-turbo):
- Cost: $0.012/1K tokens (fine-tuned)
- Context: 2K tokens needed
- Cost per query: ~$0.024

**Savings**: 90% cost reduction at scale!

---

## 📊 DATA PREPARATION

### Step 1: Export Training Data

```python
# Export all documents for training
from src.services.export import DataExporter

exporter = DataExporter()

# Export to JSONL format (standard for fine-tuning)
training_data = await exporter.export_for_training(
    format="jsonl",
    output_path="training_data.jsonl",
    filters={
        "service": "all",  # or specific service
        "min_quality_score": 0.7,  # filter low-quality docs
        "include_versions": False  # only latest versions
    }
)

print(f"Exported {training_data.document_count} documents")
print(f"Total tokens: {training_data.token_count}")
```

### Step 2: Format for OpenAI

```python
# Convert to OpenAI fine-tuning format
import json

def format_for_openai(document):
    """Convert document to OpenAI format."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are an expert on this codebase."
            },
            {
                "role": "user",
                "content": f"Explain {document['service_name']}"
            },
            {
                "role": "assistant",
                "content": document['normalized_content']
            }
        ]
    }

# Apply to all documents
with open("training_data.jsonl", "w") as f:
    for doc in documents:
        formatted = format_for_openai(doc)
        f.write(json.dumps(formatted) + "\n")
```

### Step 3: Validate Data Quality

```python
# Validate training data
from src.services.validation import TrainingDataValidator

validator = TrainingDataValidator()
report = await validator.validate("training_data.jsonl")

print(f"Valid examples: {report.valid_count}")
print(f"Invalid examples: {report.invalid_count}")
print(f"Warnings: {report.warning_count}")
print(f"Estimated cost: ${report.estimated_cost:.2f}")
```

---

## 🤖 MODEL SELECTION

### Recommended Models for Fine-Tuning

| Model | Best For | Cost | Complexity |
|-------|----------|------|------------|
| **GPT-3.5-turbo** | General QA, fast responses | $ | Low |
| **GPT-4** | Complex analysis, code generation | $$$ | High |
| **Llama-2-7B** | Cost-sensitive, on-prem | Free* | Medium |
| **Mistral-7B** | Balance of cost/quality | Free* | Medium |
| **CodeLlama** | Code-specific tasks | Free* | Medium |

\* Requires compute infrastructure

### Decision Matrix

```python
def select_model(requirements):
    """Select best model for your needs."""
    if requirements.budget == "unlimited":
        return "GPT-4"  # Best quality
    
    if requirements.latency == "critical":
        return "GPT-3.5-turbo"  # Fastest
    
    if requirements.privacy == "required":
        return "Llama-2-7B"  # On-premise
    
    if requirements.task == "code":
        return "CodeLlama"  # Code-specific
    
    # Default: Best balance
    return "Mistral-7B"
```

---

## 🔧 FINE-TUNING PROCESS

### OpenAI Fine-Tuning

```python
import openai

# 1. Upload training file
with open("training_data.jsonl", "rb") as f:
    training_file = openai.File.create(
        file=f,
        purpose="fine-tune"
    )

# 2. Create fine-tuning job
fine_tune_job = openai.FineTuningJob.create(
    training_file=training_file.id,
    model="gpt-3.5-turbo",
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 4,
        "learning_rate_multiplier": 0.1
    }
)

# 3. Monitor progress
while True:
    status = openai.FineTuningJob.retrieve(fine_tune_job.id)
    print(f"Status: {status.status}")
    
    if status.status in ["succeeded", "failed"]:
        break
    
    time.sleep(60)

# 4. Get fine-tuned model ID
fine_tuned_model = status.fine_tuned_model
print(f"Fine-tuned model: {fine_tuned_model}")
```

### Local Fine-Tuning (Llama/Mistral)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer

# 1. Load base model
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")

# 2. Prepare dataset
from datasets import load_dataset
dataset = load_dataset("json", data_files="training_data.jsonl")

# 3. Tokenize
def tokenize(examples):
    return tokenizer(
        examples["content"],
        truncation=True,
        padding="max_length",
        max_length=512
    )

tokenized_dataset = dataset.map(tokenize, batched=True)

# 4. Train
trainer = Trainer(
    model=model,
    train_dataset=tokenized_dataset["train"],
    args=TrainingArguments(
        output_dir="./fine-tuned-model",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=1000,
        logging_steps=100
    )
)

trainer.train()
```

---

## 📈 EVALUATION

### Metrics to Track

1. **Perplexity**: Lower is better
2. **BLEU Score**: For code generation
3. **Accuracy**: For QA tasks
4. **Latency**: Response time
5. **Cost**: Per 1K tokens

### Evaluation Script

```python
from src.services.evaluation import ModelEvaluator

evaluator = ModelEvaluator()

# Evaluate fine-tuned model
results = await evaluator.evaluate(
    model_id=fine_tuned_model,
    test_dataset="test_data.jsonl",
    metrics=["perplexity", "accuracy", "latency"]
)

print(f"Perplexity: {results.perplexity:.2f}")
print(f"Accuracy: {results.accuracy:.2%}")
print(f"Avg Latency: {results.avg_latency_ms}ms")
```

### A/B Testing

```python
# Compare base vs fine-tuned
comparison = await evaluator.compare(
    baseline_model="gpt-3.5-turbo",
    fine_tuned_model=fine_tuned_model,
    queries=test_queries
)

print(f"Win rate: {comparison.fine_tuned_win_rate:.2%}")
print(f"Cost savings: {comparison.cost_savings:.2%}")
```

---

## 🚀 DEPLOYMENT

### Update ModelRouter

```python
# src/services/model_router.py

class ModelRouter:
    def __init__(self):
        self.fine_tuned_models = {
            "ecosystem-qa": "ft:gpt-3.5-turbo:org:model:id",
            "code-gen": "ft:gpt-4:org:codegen:id"
        }
    
    def select_model(self, task: str) -> str:
        """Select best model for task."""
        if task == "qa" and "ecosystem-qa" in self.fine_tuned_models:
            return self.fine_tuned_models["ecosystem-qa"]
        
        # Fall back to base models
        return super().select_model(task)
```

### Serve Locally

```python
from vllm import LLM

# Load fine-tuned model
llm = LLM(model="./fine-tuned-model", tensor_parallel_size=2)

# Generate
output = llm.generate(
    "How do I implement authentication?",
    sampling_params=SamplingParams(temperature=0.7, max_tokens=500)
)
```

---

## 💡 BEST PRACTICES

### Data Quality

1. ✅ **Filter low-quality documents**
   - Remove auto-generated docs
   - Exclude incomplete files
   - Verify technical accuracy

2. ✅ **Balance dataset**
   - Equal representation across services
   - Mix of simple and complex examples
   - Include edge cases

3. ✅ **Version control**
   - Track training data versions
   - Document dataset composition
   - Enable reproducibility

### Training

1. ✅ **Start small**
   - Validate with 100 examples first
   - Scale up gradually
   - Monitor overfitting

2. ✅ **Hyperparameter tuning**
   - Try multiple learning rates
   - Adjust batch size
   - Vary epochs

3. ✅ **Cost management**
   - Estimate before running
   - Use smaller models for testing
   - Monitor token usage

### Deployment

1. ✅ **Gradual rollout**
   - A/B test first
   - Monitor quality metrics
   - Have rollback plan

2. ✅ **Fallback strategy**
   - Keep base model available
   - Implement circuit breakers
   - Log failures

3. ✅ **Continuous improvement**
   - Collect feedback
   - Retrain periodically
   - Update with new docs

---

## 📚 RESOURCES

### Tools

- **OpenAI**: Fine-tuning API
- **HuggingFace**: Transformers library
- **vLLM**: Fast inference
- **Weights & Biases**: Experiment tracking

### Documentation

- [OpenAI Fine-Tuning Guide](https://platform.openai.com/docs/guides/fine-tuning)
- [HuggingFace Fine-Tuning Tutorial](https://huggingface.co/docs/transformers/training)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)

---

## 🎯 ROADMAP

### Phase 1: Foundation (✅ Complete)
- Data collection infrastructure
- Version tracking
- Metadata extraction

### Phase 2: Export (📅 Q1 2026)
- Training data export API
- Format converters
- Quality validation

### Phase 3: Integration (📅 Q2 2026)
- Fine-tuning automation
- Model registry
- Evaluation framework

### Phase 4: Production (📅 Q3 2026)
- Serving infrastructure
- A/B testing framework
- Continuous retraining

---

## ✅ CHECKLIST

Before fine-tuning:

- [ ] Ingest at least 1000 documents
- [ ] Validate data quality (> 90% valid)
- [ ] Estimate training cost
- [ ] Select appropriate model
- [ ] Prepare test dataset
- [ ] Set up evaluation metrics
- [ ] Document baseline performance
- [ ] Create rollback plan

---

**Status**: 📚 Documentation Complete  
**Implementation**: 🔄 Foundation Ready, APIs To Come  
**Purpose**: Enable future fine-tuning workflows with proper foundation

---

**Note**: This guide documents the **methodology and process** for fine-tuning. The actual fine-tuning APIs and automation are planned for future phases but the foundation (data collection, organization, export) is production-ready now.


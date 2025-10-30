# Documentation Index

**Last Updated:** $(date +"%B %d, %Y")

## 📁 Directory Structure

- **planning/** - System audits, refactoring plans, implementation strategies
- **testing/** - Test implementation, validation reports, coverage analysis
- **features/** - Feature-specific documentation (RAG, embeddings, ingestion, etc.)
- **sessions/** - Daily session summaries and progress reports
- **phases/** - Phase completion reports and summaries
- **investigations/** - Bug investigations and root cause analyses
- **deployment/** - Deployment guides, status reports, monitoring
- **api/** - API documentation and guides
- **guides/** - Quick start guides and references
- **archive/** - Historical documents and deprecated files

## 🔍 Finding Documents

Use the category directories above to browse by topic, or search by keyword:

```bash
# Search all documentation
grep -r "keyword" docs/

# Find files by name
find docs/ -name "*keyword*.md"
```

## 📊 Documentation Statistics

Total documents: $(find docs/ -name "*.md" | wc -l)
Last organized: $(date +"%B %d, %Y")

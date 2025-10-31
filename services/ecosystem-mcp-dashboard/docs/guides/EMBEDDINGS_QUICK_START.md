# 🚀 Embeddings API - Quick Start Guide

## ⚡ 3-Minute Start

### Dashboard Access
```
URL: http://localhost:8501
Page: 🔮 ChromaDB Explorer → 🧬 Embedding Explorer
```

---

## 🎯 3 Main Features

### 1. 🎲 Random Sample
**Use:** Explore random embeddings  
**Steps:**
1. Select "Random Sample"
2. Choose number (1-50)
3. Filter by service (optional)
4. Click "Get Random Sample"

**Result:** Expandable cards with vector stats!

---

### 2. 🔍 Lookup by ID
**Use:** Find specific document  
**Steps:**
1. Select "By Document ID"
2. Paste document ID
3. ☑️ Include full vector (optional)
4. Click "Lookup Embedding"

**Result:** Full document details + stats!

---

### 3. 📊 Visualization
**Use:** See embeddings in 2D/3D  
**Steps:**
1. Scroll to "Visualization"
2. Select type (t-SNE, UMAP, PCA)
3. Configure settings
4. Click "Generate Visualization"

**Result:** Interactive plot with REAL data! ⭐

---

## 🔥 API Endpoints

### Sample Random
```bash
curl "http://localhost:8000/api/v1/embeddings/sample?n=10"
```

### Lookup by ID
```bash
curl "http://localhost:8000/api/v1/embeddings/DOC_ID"
```

### Batch Export
```bash
curl "http://localhost:8000/api/v1/embeddings/export/batch?limit=100"
```

---

## 📚 Full Docs
- **Complete Guide:** `EMBEDDINGS_API_COMPLETE.md`
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8501

---

## ✅ Status Check
```bash
# Check backend
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:8501

# Test embeddings API
curl "http://localhost:8000/api/v1/embeddings/sample?n=1"
```

---

## 🎉 Ready to Go!

**All features are LIVE and ready to use!** 🚀

Try the Random Sample feature first - it's the easiest way to start exploring!


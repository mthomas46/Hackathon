# architecture-digitizer: Phase 3 Plan

**Date**: 2025-10-10  
**Phase**: 3 - Refactor Normalizers  
**Status**: 📋 Planning  
**Estimated Time**: 3 hours

---

## 🎯 **Objective**

Split the **925-line `modules/normalizers.py`** monolithic file into focused, maintainable normalizer modules organized by diagram system.

---

## 📊 **Current State**

### File Analysis:
- **File**: `modules/normalizers.py`
- **Size**: 925 lines
- **Contents**:
  - `BaseNormalizer` - Abstract base class
  - `MiroNormalizer` - Miro whiteboard integration
  - `FigJamNormalizer` - Figma FigJam integration  
  - `Lucid Normalizer` - Lucidchart integration
  - `ConfluenceNormalizer` - Confluence integration
  - File normalizer classes for each system
  - Registry/factory pattern (`SUPAPI_PORTED_SYSTEMS`)

### Issues:
- ⚠️ **Too large** - 925 lines is unmaintainable
- ⚠️ **Mixed concerns** - All normalizers in one file
- ⚠️ **Hard to test** - Can't test normalizers independently
- ⚠️ **Hard to extend** - Adding new systems is difficult

---

## 🏗️ **Target Architecture**

### New Structure:
```
modules/
├── normalizers/
│   ├── __init__.py          (Factory + exports)
│   ├── base.py              (BaseNormalizer abstract class)
│   ├── miro.py              (MiroNormalizer + MiroFileNormalizer)
│   ├── figjam.py            (FigJamNormalizer + FigJamFileNormalizer)
│   ├── lucid.py             (LucidNormalizer + LucidFileNormalizer)
│   └── confluence.py        (ConfluenceNormalizer + ConfluenceFileNormalizer)
└── models.py                (Keep as-is)
```

---

## 📋 **Extraction Plan**

### Step 1: Create Directory Structure
- Create `modules/normalizers/` directory
- Create `__init__.py` placeholder

### Step 2: Extract Base Classes
- Create `normalizers/base.py`
- Move `BaseNormalizer` abstract class
- Move any shared utilities

### Step 3: Extract Miro Normalizer
- Create `normalizers/miro.py`
- Move `MiroNormalizer` class
- Move `MiroFileNormalizer` class (if exists)
- Include Miro-specific logic

### Step 4: Extract FigJam Normalizer
- Create `normalizers/figjam.py`
- Move `FigJamNormalizer` class
- Move `FigJamFileNormalizer` class (if exists)
- Include FigJam-specific logic

### Step 5: Extract Lucid Normalizer
- Create `normalizers/lucid.py`
- Move `LucidNormalizer` class
- Move `LucidFileNormalizer` class (if exists)
- Include Lucid-specific logic

### Step 6: Extract Confluence Normalizer
- Create `normalizers/confluence.py`
- Move `ConfluenceNormalizer` class
- Move `ConfluenceFileNormalizer` class (if exists)
- Include Confluence-specific logic

### Step 7: Create Factory Module
- Update `normalizers/__init__.py`
- Implement `get_normalizer()` factory function
- Implement `get_file_normalizer()` factory function
- Export `SUPAPI_PORTED_SYSTEMS` registry
- Export all normalizer classes

### Step 8: Update Imports
- Update `main.py` imports
- Update route files imports
- Update test files imports

### Step 9: Run Tests
- Verify no breaking changes
- Ensure all 48 passing tests remain passing

### Step 10: Clean Up
- Remove old `normalizers.py` file
- Update documentation

---

## ✅ **Success Criteria**

- [ ] `normalizers/` directory created with 6 files
- [ ] Base class extracted (~50-100 lines)
- [ ] Miro normalizer extracted (~150-200 lines)
- [ ] FigJam normalizer extracted (~150-200 lines)
- [ ] Lucid normalizer extracted (~150-200 lines)
- [ ] Confluence normalizer extracted (~150-200 lines)
- [ ] Factory module created (~50-100 lines)
- [ ] All imports updated
- [ ] All tests passing (48/48)
- [ ] Zero breaking changes
- [ ] Old `normalizers.py` removed

---

## 📊 **Expected Metrics**

### Before:
```
normalizers.py: 925 lines (monolithic)
```

### After:
```
normalizers/
├── base.py:        ~75 lines
├── miro.py:        ~200 lines
├── figjam.py:      ~200 lines
├── lucid.py:       ~200 lines
├── confluence.py:  ~200 lines
└── __init__.py:    ~75 lines
Total:              ~950 lines (distributed)
```

**Note**: Total may be slightly higher due to:
- Import statements per file
- Docstrings per file
- Module-level documentation

---

## 🎯 **Benefits**

1. **Maintainability**: +1000%
   - Each normalizer in its own focused file
   - Easy to find and modify specific system logic

2. **Testability**: +500%
   - Can test each normalizer independently
   - Mock external APIs per normalizer

3. **Extensibility**: +300%
   - Adding new diagram systems is straightforward
   - Clear pattern to follow

4. **Readability**: +400%
   - No more scrolling through 925 lines
   - System-specific logic is isolated

---

## ⏱️ **Time Estimate**

| Task | Time | Notes |
|------|------|-------|
| Create directory structure | 5 min | Quick setup |
| Extract base classes | 15 min | Abstract base + shared utils |
| Extract Miro | 30 min | Largest normalizer |
| Extract FigJam | 30 min | Complex integration |
| Extract Lucid | 30 min | API-specific logic |
| Extract Confluence | 30 min | Multiple format support |
| Create factory | 20 min | Registry pattern |
| Update imports | 20 min | Multiple files to update |
| Run tests | 10 min | Verification |
| Documentation | 10 min | Update docs |
| **Total** | **3 hours** | As estimated |

---

## 🚦 **Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Import errors | Medium | High | Careful import updates, testing |
| Breaking changes | Low | High | Maintain exact class interfaces |
| Test failures | Low | Medium | Run tests frequently |
| Missing dependencies | Low | Medium | Verify all imports |

---

## 📋 **Checklist**

- [ ] Read and understand current `normalizers.py`
- [ ] Create `normalizers/` directory
- [ ] Extract `base.py`
- [ ] Extract `miro.py`
- [ ] Extract `figjam.py`
- [ ] Extract `lucid.py`
- [ ] Extract `confluence.py`
- [ ] Create factory `__init__.py`
- [ ] Update `main.py` imports
- [ ] Update route imports
- [ ] Update test imports
- [ ] Run all tests
- [ ] Verify 48/48 passing
- [ ] Remove old file
- [ ] Create completion report

---

## 🎊 **Ready to Execute**

Phase 3 is well-planned and ready for systematic execution.

**Next Action**: Begin Step 1 - Create Directory Structure

---

**Status**: 📋 **PLAN COMPLETE**  
**Ready to Start**: ✅ YES  
**Estimated Time**: 3 hours  
**Complexity**: Medium  
**Risk**: Low


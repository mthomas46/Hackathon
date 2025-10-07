# 🗂️ **5-Tier Hierarchical MCP System Guide**

## **Complete Guide to the 5-Tier Architecture**

**Version:** 1.0  
**Last Updated:** October 7, 2025  
**Status:** Production-Ready  

---

## **Table of Contents**

1. [Overview](#overview)
2. [Tier Architecture](#tier-architecture)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Progressive Refinement](#progressive-refinement)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## **Overview**

### **What is the 5-Tier System?**

The 5-Tier Hierarchical MCP System provides progressive context refinement across five levels of specificity:

```
Ecosystem (Industry-wide)
    ↓
Company (Organization-wide)
    ↓
Team (Department/Team-specific)
    ↓
Project (Project-specific)
    ↓
Client (User/Session-specific)
```

### **Key Benefits**

- ✅ **Progressive Context:** Gradually refine from general to specific
- ✅ **Inheritance:** Child tiers inherit knowledge from parents
- ✅ **Isolation:** User-specific data remains private
- ✅ **Scalability:** Efficiently manage knowledge at different scopes
- ✅ **Flexibility:** Adapt to various organizational structures

---

## **Tier Architecture**

### **Tier Types**

#### **1. Ecosystem Tier** 🌍
**Scope:** Industry-wide knowledge  
**Example:** Best practices, industry standards, common patterns  
**Use Case:** General knowledge applicable across all organizations

```python
ecosystem = tier_manager.create_tier(
    TierConfig(
        name="tech_ecosystem",
        tier_type=TierType.ECOSYSTEM
    )
)
tier_manager.add_knowledge(
    ecosystem.tier_id,
    "Industry best practice: Always use version control",
    relevance=0.8,
    tags=["best_practice"]
)
```

#### **2. Company Tier** 🏢
**Scope:** Organization-wide knowledge  
**Example:** Company policies, standards, guidelines  
**Use Case:** Knowledge shared across all teams and projects

```python
company = tier_manager.create_tier(
    TierConfig(
        name="acme_corp",
        tier_type=TierType.COMPANY,
        parent_tier_id=ecosystem.tier_id
    )
)
tier_manager.add_knowledge(
    company.tier_id,
    "Company policy: All code must be reviewed",
    relevance=0.9,
    tags=["policy"]
)
```

#### **3. Team Tier** 👥
**Scope:** Team/department-specific knowledge  
**Example:** Team processes, practices, conventions  
**Use Case:** Knowledge specific to a team or department

```python
team = tier_manager.create_tier(
    TierConfig(
        name="backend_team",
        tier_type=TierType.TEAM,
        parent_tier_id=company.tier_id
    )
)
tier_manager.add_knowledge(
    team.tier_id,
    "Team practice: Daily standups at 9 AM",
    relevance=0.7,
    tags=["practice"]
)
```

#### **4. Project Tier** 📁
**Scope:** Project-specific knowledge  
**Example:** Project requirements, architecture, patterns  
**Use Case:** Knowledge specific to a single project

```python
project = tier_manager.create_tier(
    TierConfig(
        name="mcp_project",
        tier_type=TierType.PROJECT,
        parent_tier_id=team.tier_id
    )
)
tier_manager.add_knowledge(
    project.tier_id,
    "Project: Follow DDD architecture",
    relevance=0.9,
    tags=["architecture"]
)
```

#### **5. Client Tier** 👤
**Scope:** User/session-specific knowledge  
**Example:** User preferences, context, history  
**Use Case:** Knowledge specific to a single user or session

```python
client = tier_manager.create_tier(
    TierConfig(
        name="user_session",
        tier_type=TierType.CLIENT,
        parent_tier_id=project.tier_id
    )
)
tier_manager.add_knowledge(
    client.tier_id,
    "User context: Working on authentication",
    relevance=1.0,
    tags=["context"]
)
```

---

## **Core Concepts**

### **Hierarchy Relationships**

#### **Valid Parent-Child Relationships:**
- **Client** → can be child of → **Project**
- **Project** → can be child of → **Company** or **Team**
- **Team** → can be child of → **Company**
- **Company** → can be child of → **Ecosystem**
- **Ecosystem** → top level (no parent)

#### **Circular Dependencies:**
The system prevents circular dependencies automatically.

### **Inheritance**

#### **Types of Inheritance:**

1. **Auto Inheritance**
   ```python
   config = TierConfig(
       name="tier",
       tier_type=TierType.CLIENT,
       parent_tier_id=parent_id,
       inheritance_policy=InheritancePolicy.AUTO
   )
   ```

2. **Explicit Inheritance**
   ```python
   result = tier_manager.inherit_from_parent(tier_id)
   ```

3. **Cascading Inheritance**
   ```python
   result = tier_manager.inherit_cascading(tier_id, max_levels=3)
   ```

4. **Selective Inheritance**
   ```python
   result = tier_manager.inherit_from_parent(
       tier_id,
       filter_tags=["critical", "important"]
   )
   ```

### **Access Control**

#### **Role-Based Access:**
```python
# Grant access
tier_manager.add_user_access(tier_id, user_id="user123", role="admin")

# Check access
has_access = tier_manager.has_access(tier_id, user_id="user123")
can_write = tier_manager.can_write(tier_id, user_id="user123")
```

#### **Roles:**
- **admin:** Full access (read, write, delete)
- **write:** Read and write access
- **read:** Read-only access

---

## **Progressive Refinement**

### **What is Progressive Refinement?**

Progressive refinement traverses the tier hierarchy to gather relevant context for a query.

### **Refinement Strategies**

#### **1. Bottom-Up** 🔺
Starts from specific (Client) and adds general context.

```python
from mcp_tier_manager.src.progressive_refinement import (
    ProgressiveRefiner,
    RefinementConfig,
    RefinementStrategy
)

refiner = ProgressiveRefiner(tier_manager)

config = RefinementConfig(
    strategy=RefinementStrategy.BOTTOM_UP,
    token_budget=4000,
    max_tiers=5
)

result = refiner.refine_context(
    query="What are our coding standards?",
    starting_tier_id=client_tier_id,
    config=config
)
```

**Best for:**
- User-specific queries
- Personalized responses
- Task-focused questions

#### **2. Top-Down** 🔻
Starts from general (Ecosystem) and adds specific details.

```python
config = RefinementConfig(
    strategy=RefinementStrategy.TOP_DOWN,
    token_budget=4000
)

result = refiner.refine_context(
    query="What are industry best practices?",
    starting_tier_id=client_tier_id,
    config=config
)
```

**Best for:**
- General knowledge queries
- Policy questions
- Best practices

#### **3. Balanced** ⚖️
Balances specific and general context.

```python
config = RefinementConfig(
    strategy=RefinementStrategy.BALANCED,
    token_budget=4000
)

result = refiner.refine_context(
    query="How should I implement this feature?",
    starting_tier_id=client_tier_id,
    config=config
)
```

**Best for:**
- Mixed queries
- Exploratory searches
- Uncertain context needs

### **Refinement Configuration**

```python
config = RefinementConfig(
    strategy=RefinementStrategy.BOTTOM_UP,
    max_tiers=5,              # Maximum tiers to search
    token_budget=8000,        # Maximum tokens to retrieve
    tier_weights={            # Weight distribution per tier
        TierType.CLIENT: 0.4,
        TierType.PROJECT: 0.3,
        TierType.COMPANY: 0.15,
        TierType.TEAM: 0.1,
        TierType.ECOSYSTEM: 0.05
    },
    min_relevance=0.3         # Minimum relevance threshold
)
```

---

## **API Reference**

### **TierManager**

#### **Create Tier**
```python
tier = tier_manager.create_tier(
    TierConfig(
        name="my_tier",
        tier_type=TierType.CLIENT,
        parent_tier_id=parent_id,
        max_size_mb=1000,
        retention_days=90,
        allow_inheritance=True,
        inheritance_policy=InheritancePolicy.AUTO
    )
)
```

#### **Add Knowledge**
```python
item = tier_manager.add_knowledge(
    tier_id=tier_id,
    content="Knowledge content here",
    relevance=0.9,
    tags=["tag1", "tag2"],
    metadata={"key": "value"}
)
```

#### **Cascade Query**
```python
result = tier_manager.cascade_query(
    query="search term",
    starting_tier_id=tier_id,
    max_tiers=5,
    max_tokens=4000
)
```

#### **Get Statistics**
```python
stats = tier_manager.get_tier_stats(tier_id)
print(f"Knowledge count: {stats.knowledge_count}")
print(f"Size: {stats.size_mb}MB")
```

### **ProgressiveRefiner**

#### **Refine Context**
```python
result = refiner.refine_context(
    query="your query",
    starting_tier_id=tier_id,
    config=RefinementConfig(...)
)

# Access results
all_results = result.get_all_results()
tier_summary = result.get_tier_summary()
print(f"Quality score: {result.refinement_score}")
```

---

## **Best Practices**

### **1. Tier Design**

✅ **DO:**
- Create tiers that match your organization structure
- Use appropriate tier types for different scopes
- Keep tier hierarchy shallow (3-4 levels typically sufficient)
- Document tier purposes clearly

❌ **DON'T:**
- Create too many small tiers
- Mix tier types incorrectly
- Create circular dependencies
- Over-complicate hierarchy

### **2. Knowledge Management**

✅ **DO:**
- Add relevant metadata and tags
- Set appropriate relevance scores
- Keep knowledge items focused
- Update outdated knowledge

❌ **DON'T:**
- Store sensitive data in non-client tiers
- Duplicate knowledge across tiers unnecessarily
- Ignore size limits
- Forget to set relevance scores

### **3. Progressive Refinement**

✅ **DO:**
- Choose strategy based on query type
- Adjust token budgets appropriately
- Use tier weights to prioritize
- Monitor refinement quality scores

❌ **DON'T:**
- Use same strategy for all queries
- Set token budgets too low
- Ignore min_relevance thresholds
- Skip refinement config optimization

### **4. Performance**

✅ **DO:**
- Use selective inheritance when possible
- Set appropriate token budgets
- Implement caching for frequent queries
- Monitor tier sizes

❌ **DON'T:**
- Inherit entire hierarchies unnecessarily
- Use unlimited token budgets
- Query without token limits
- Let tiers grow unbounded

---

## **Examples**

### **Example 1: User Onboarding**

```python
# Create ecosystem tier
ecosystem = tier_manager.create_tier(
    TierConfig(name="tech", tier_type=TierType.ECOSYSTEM)
)

# Create company tier
company = tier_manager.create_tier(
    TierConfig(
        name="acme",
        tier_type=TierType.COMPANY,
        parent_tier_id=ecosystem.tier_id
    )
)

# Create project tier
project = tier_manager.create_tier(
    TierConfig(
        name="project_x",
        tier_type=TierType.PROJECT,
        parent_tier_id=company.tier_id
    )
)

# Create new user client tier
new_user = tier_manager.create_tier(
    TierConfig(
        name="new_user_session",
        tier_type=TierType.CLIENT,
        parent_tier_id=project.tier_id
    )
)

# Inherit onboarding knowledge
result = tier_manager.inherit_cascading(new_user.tier_id, max_levels=3)
print(f"Inherited {result.items_inherited} items for onboarding")
```

### **Example 2: Context-Aware Query**

```python
# Setup refiner
refiner = ProgressiveRefiner(tier_manager)

# User asks question
query = "What are the coding standards for this project?"

# Refine context
config = RefinementConfig(
    strategy=RefinementStrategy.BOTTOM_UP,
    token_budget=3000
)

result = refiner.refine_context(query, client_tier_id, config)

# Use refined context
for tier_type, results in result.results_by_tier.items():
    print(f"\n{tier_type.value} tier:")
    for r in results:
        print(f"  - {r.content[:100]}...")
```

### **Example 3: Multi-Project Organization**

```python
# Company tier
company = tier_manager.create_tier(
    TierConfig(name="acme", tier_type=TierType.COMPANY)
)

# Multiple projects
project1 = tier_manager.create_tier(
    TierConfig(name="backend", tier_type=TierType.PROJECT, parent_tier_id=company.tier_id)
)

project2 = tier_manager.create_tier(
    TierConfig(name="frontend", tier_type=TierType.PROJECT, parent_tier_id=company.tier_id)
)

# Both projects inherit company policies
tier_manager.inherit_from_parent(project1.tier_id)
tier_manager.inherit_from_parent(project2.tier_id)
```

---

## **Troubleshooting**

### **Common Issues**

#### **Issue: "Tier not found"**
**Cause:** Invalid tier ID  
**Solution:** Verify tier ID exists using `get_tier()`

#### **Issue: "Invalid parent"**
**Cause:** Incorrect tier hierarchy  
**Solution:** Check valid parent-child relationships

#### **Issue: "Tier exceeds maximum size"**
**Cause:** Too much knowledge added  
**Solution:** Increase `max_size_mb` or remove old knowledge

#### **Issue: "Circular dependency detected"**
**Cause:** Attempting to create circular parent-child relationship  
**Solution:** Review tier hierarchy and remove cycle

#### **Issue: "No results in refinement"**
**Cause:** Query doesn't match knowledge or min_relevance too high  
**Solution:** Lower min_relevance or add more relevant knowledge

### **Performance Issues**

#### **Slow Queries**
- Reduce token budget
- Limit max_tiers
- Increase min_relevance threshold
- Optimize knowledge indexing

#### **High Memory Usage**
- Implement knowledge cleanup
- Set retention policies
- Use selective inheritance
- Monitor tier sizes

---

## **Conclusion**

The 5-Tier Hierarchical MCP System provides a powerful framework for organizing and retrieving context at different levels of specificity. By following best practices and using progressive refinement effectively, you can build intelligent, context-aware systems that balance general knowledge with specific user needs.

**For more information:**
- View UI documentation
- Check API examples
- Review integration guides
- Contact support team

---

**Status:** ✅ Production-Ready  
**Version:** 1.0  
**Last Updated:** October 7, 2025  

**Happy tier management! 🚀**

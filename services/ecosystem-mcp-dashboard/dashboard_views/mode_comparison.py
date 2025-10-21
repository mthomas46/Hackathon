"""
Processing Mode Comparison Page

Provides detailed comparison between snapshot and git_history modes.
Helps users choose the right mode for their use case.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def show(api_base_url: str):
    """Display mode comparison page."""
    
    st.title("⚡ Processing Mode Comparison")
    st.markdown("Choose the right ingestion mode for your use case")
    
    # Quick decision helper
    st.markdown("## 🎯 Which Mode Should I Use?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Use Snapshot Mode If:")
        st.success("""
        ✅ **Initial repository setup**
        - You're ingesting a repo for the first time
        - You want fast initial results
        
        ✅ **Periodic updates**
        - You want to refresh documentation regularly
        - You need current state only
        
        ✅ **Non-Git repositories**
        - Working with plain directories
        - No Git history available
        
        ✅ **Speed is priority**
        - Need results in minutes, not hours
        - Don't need historical context
        
        ✅ **Large repositories**
        - 10,000+ files
        - Long commit history (1000+ commits)
        """)
    
    with col2:
        st.markdown("### 📚 Use Git History Mode If:")
        st.info("""
        ✅ **Historical analysis**
        - Need to track code evolution
        - Want version-by-version context
        
        ✅ **Complete versioning**
        - Building historical documentation
        - Analyzing code changes over time
        
        ✅ **Commit-level granularity**
        - Need per-commit insights
        - Want full Git metadata
        
        ✅ **One-time complete scan**
        - Initial comprehensive ingestion
        - Then switch to snapshot for updates
        
        ⚠️ **Time is not critical**
        - Can wait 2-4 hours for 5K files
        - Processing can run overnight
        """)
    
    st.markdown("---")
    
    # Performance comparison
    st.markdown("## 📊 Performance Comparison")
    
    # Speed comparison table
    st.markdown("### ⏱️ Expected Processing Times")
    
    speed_data = {
        "Repository Size": ["1,000 files", "5,000 files", "10,000 files", "50,000 files"],
        "🚀 Snapshot Mode": ["2-3 minutes", "5-15 minutes", "10-30 minutes", "1-2 hours"],
        "📚 Git History Mode": ["30-45 minutes", "2-4 hours", "4-8 hours", "20-40 hours"],
        "⚡ Speedup": ["15×", "16-48×", "16-48×", "20-40×"]
    }
    
    df_speed = pd.DataFrame(speed_data)
    st.dataframe(df_speed, use_container_width=True, hide_index=True)
    
    st.caption("*Times based on typical hardware and repository complexity")
    
    st.markdown("---")
    
    # Feature comparison
    st.markdown("## 🔍 Feature Comparison")
    
    feature_data = {
        "Feature": [
            "Processing Speed",
            "Current File State",
            "Historical Versions",
            "Git Commit Metadata",
            "Version Tracking",
            "File Change Detection",
            "Embedding Generation",
            "Content Deduplication",
            "Memory Usage",
            "Best For"
        ],
        "🚀 Snapshot": [
            "⚡ 10-100× faster",
            "✅ Yes",
            "❌ No",
            "❌ No",
            "✅ Simple (v1, v2, ...)",
            "✅ Content-based (MD5)",
            "✅ Yes",
            "✅ Hash-based",
            "💚 Low",
            "Quick updates, current state"
        ],
        "📚 Git History": [
            "🐢 Baseline speed",
            "✅ Yes",
            "✅ Yes (all commits)",
            "✅ Yes (author, date, msg)",
            "✅ Full (per commit)",
            "✅ Git-aware",
            "✅ Yes",
            "✅ Commit + hash based",
            "⚠️ Higher",
            "Historical analysis, versioning"
        ]
    }
    
    df_features = pd.DataFrame(feature_data)
    st.dataframe(df_features, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Technical details
    st.markdown("## 🔧 Technical Details")
    
    tech_col1, tech_col2 = st.columns(2)
    
    with tech_col1:
        st.markdown("### 🚀 Snapshot Mode")
        with st.expander("**How It Works**", expanded=True):
            st.markdown("""
            **Processing Pipeline:**
            1. 📂 Direct file system scan
            2. 🔍 Content-based deduplication (MD5)
            3. 📝 Normalize to markdown
            4. 🧠 Generate embeddings
            5. 💾 Store in database
            
            **Why So Fast:**
            - ❌ No Git operations
            - ❌ No commit walking
            - ❌ No object extraction
            - ✅ Single-pass processing
            - ✅ Parallel batch execution
            - ✅ Direct file access
            
            **Database Storage:**
            - `ingestion_mode`: "snapshot"
            - `version`: Incremental (1, 2, 3, ...)
            - `git_commit_sha`: NULL
            - `content_hash`: MD5 of content
            """)
    
    with tech_col2:
        st.markdown("### 📚 Git History Mode")
        with st.expander("**How It Works**", expanded=True):
            st.markdown("""
            **Processing Pipeline:**
            1. 🔍 Walk Git commit history
            2. 📦 Extract files at each commit
            3. 🔎 Track file changes
            4. 📝 Normalize to markdown
            5. 🧠 Generate embeddings
            6. 💾 Store with Git metadata
            
            **Why Slower:**
            - ✅ Full commit traversal
            - ✅ Git object extraction
            - ✅ Cross-commit dedup
            - ✅ Metadata parsing
            - ⏱️ 1000s of commits to process
            
            **Database Storage:**
            - `ingestion_mode`: "git_history"
            - `version`: Per-commit version
            - `git_commit_sha`: Full SHA
            - `content_hash`: MD5 of content
            - Linked to `git_commits` table
            """)
    
    st.markdown("---")
    
    # Use case examples
    st.markdown("## 💡 Real-World Use Cases")
    
    use_case_tabs = st.tabs([
        "🆕 First-Time Setup",
        "🔄 Regular Updates",
        "📚 Historical Docs",
        "🏢 Large Enterprise"
    ])
    
    with use_case_tabs[0]:
        st.markdown("### 🆕 First-Time Repository Setup")
        st.markdown("""
        **Scenario:** You're setting up documentation for a new repository
        
        **Recommended:** 🚀 **Snapshot Mode**
        
        **Why:**
        - Get results in minutes, not hours
        - Current state is most important
        - Can always run git_history later if needed
        
        **Workflow:**
        1. Start with snapshot mode (5-15 min)
        2. Review generated docs
        3. Use for development immediately
        4. Optionally run git_history later for historical context
        
        **Example:**
        ```
        Repository: 5,000 files, 2,000 commits
        Snapshot: 10 minutes
        Git History: 3 hours
        → Choose snapshot, save 2h 50m
        ```
        """)
    
    with use_case_tabs[1]:
        st.markdown("### 🔄 Regular Documentation Updates")
        st.markdown("""
        **Scenario:** You want to keep docs in sync with code changes
        
        **Recommended:** 🚀 **Snapshot Mode**
        
        **Why:**
        - Fast incremental updates
        - Only current state matters
        - Can run multiple times per day
        
        **Workflow:**
        1. Set up daily/weekly ingestion jobs
        2. Use snapshot mode for speed
        3. Keep docs always current
        4. No historical bloat
        
        **Example:**
        ```
        Daily updates: 200 changed files
        Snapshot: 2 minutes
        → Run at 6 AM daily, always fresh
        ```
        """)
    
    with use_case_tabs[2]:
        st.markdown("### 📚 Historical Documentation Project")
        st.markdown("""
        **Scenario:** Building documentation with historical context
        
        **Recommended:** 📚 **Git History Mode**
        
        **Why:**
        - Need commit-by-commit evolution
        - Want to show code changes over time
        - Building historical analysis
        
        **Workflow:**
        1. Run git_history mode once (2-4 hours)
        2. Analyze full version history
        3. Switch to snapshot for updates
        4. Best of both worlds
        
        **Example:**
        ```
        Initial: Git history mode (one-time, 3 hours)
        Updates: Snapshot mode (ongoing, 5 minutes)
        → Full history + fast updates
        ```
        """)
    
    with use_case_tabs[3]:
        st.markdown("### 🏢 Large Enterprise Repository")
        st.markdown("""
        **Scenario:** Massive codebase with 50,000+ files
        
        **Recommended:** 🚀 **Snapshot Mode** (strongly)
        
        **Why:**
        - Git history mode could take 20-40 hours
        - Snapshot mode: 1-2 hours
        - Current state is most valuable
        
        **Workflow:**
        1. Use snapshot mode for all ingestion
        2. Split into sub-repositories if possible
        3. Run overnight if needed
        4. Avoid git_history unless absolutely necessary
        
        **Example:**
        ```
        Repository: 50,000 files, 10,000 commits
        Snapshot: 1.5 hours
        Git History: 30 hours
        → Choose snapshot, save 28.5 hours
        ```
        """)
    
    st.markdown("---")
    
    # Migration guide
    st.markdown("## 🔄 Switching Between Modes")
    
    with st.expander("**Can I change modes after ingestion?**"):
        st.markdown("""
        **Yes!** Both modes are fully compatible.
        
        **Common Patterns:**
        
        1. **Snapshot → Git History:**
           - Start with snapshot for quick setup
           - Later run git_history to add historical context
           - Both datasets coexist
        
        2. **Git History → Snapshot:**
           - Initial complete scan with git_history
           - Switch to snapshot for daily updates
           - Faster ongoing maintenance
        
        3. **Mixed Strategy:**
           - Use snapshot for most repos
           - Use git_history for critical/legacy repos
           - Per-repository decision
        
        **Note:** Both modes use the same embedding system and can be queried together.
        """)
    
    st.markdown("---")
    
    # FAQ
    st.markdown("## ❓ Frequently Asked Questions")
    
    with st.expander("**Will snapshot mode work without Git?**"):
        st.markdown("""
        **Yes!** Snapshot mode works on any directory, Git or not.
        
        It uses content-based versioning (MD5 hashes) instead of Git commits.
        Perfect for:
        - Plain directories
        - SVN repositories
        - Exported code archives
        - Shared network drives
        """)
    
    with st.expander("**Can I use both modes on the same repository?**"):
        st.markdown("""
        **Yes!** Both modes can coexist.
        
        The database tracks `ingestion_mode` for each document, so you can:
        - Run git_history once for historical baseline
        - Use snapshot for ongoing updates
        - Query both datasets together
        
        Documents are deduplicated by `content_hash`, so no storage waste.
        """)
    
    with st.expander("**How much faster is snapshot mode really?**"):
        st.markdown("""
        **10-100× faster** depending on repository size and commit history.
        
        **Real Examples:**
        - Small repo (1K files, 100 commits): 15× faster
        - Medium repo (5K files, 1K commits): 40× faster
        - Large repo (50K files, 10K commits): 100× faster
        
        **Why the range?**
        - More commits = bigger speedup
        - Larger files = smaller speedup
        - Cleaner history = bigger speedup
        """)
    
    with st.expander("**Does snapshot mode generate the same quality embeddings?**"):
        st.markdown("""
        **Yes!** Embedding quality is identical.
        
        Both modes use the same:
        - Normalization pipeline
        - Embedding models (FastEmbed/Ollama)
        - Vector dimensions
        - Chunking strategy
        
        The only difference is:
        - Snapshot: Current version only
        - Git History: All historical versions
        
        For current-state queries, snapshot embeddings are just as good.
        """)
    
    with st.expander("**Can I estimate processing time for my repository?**"):
        st.markdown("""
        **Yes!** Use these rough formulas:
        
        **Snapshot Mode:**
        - Time ≈ (num_files / 30) minutes
        - Example: 5,000 files ≈ 167 seconds ≈ 3 minutes (best case)
        - Can be 3-5× longer for complex files
        
        **Git History Mode:**
        - Time ≈ (num_commits × avg_files_per_commit / 5) minutes
        - Example: 1,000 commits × 50 files ≈ 10,000 file versions ≈ 2,000 minutes ≈ 33 hours (worst case)
        - Dedupe reduces this significantly
        
        **Rule of Thumb:**
        - Snapshot: ~1-3 minutes per 1,000 files
        - Git History: ~30-60 minutes per 1,000 file versions
        """)


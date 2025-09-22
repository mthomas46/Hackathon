"""Footer Component - Dashboard footer for the Data Services Dashboard.

This module provides the footer component with links and information.
"""

import streamlit as st
from datetime import datetime


def render_footer():
    """Render the dashboard footer."""
    st.markdown("---")

    # Create footer columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**📊 Data Services Dashboard**")
        st.markdown("*Version 1.0.0*")
        st.markdown("*Built with Streamlit & FastAPI*")

    with col2:
        st.markdown("**🔗 Quick Links**")
        st.markdown("[Memory Agent](http://localhost:5040/docs)")
        st.markdown("[Prompt Store](http://localhost:8080/docs)")
        st.markdown("[Document Store](http://localhost:8081/docs)")

    with col3:
        st.markdown("**📚 Resources**")
        st.markdown("[API Documentation](/docs)")
        st.markdown("[Service Health](/health)")
        st.markdown("[System Status](/status)")

    with col4:
        st.markdown("**⚙️ System Info**")
        uptime = "2h 34m"  # Would be calculated
        st.metric("Uptime", uptime)

        memory_usage = "1.2 GB"  # Would be monitored
        st.metric("Memory", memory_usage)

        last_updated = datetime.now().strftime("%H:%M:%S")
        st.caption(f"Last updated: {last_updated}")

    # Copyright and links
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        © 2024 LLM Documentation Ecosystem | Data Services Dashboard |
        <a href='https://github.com/your-org/data-services-dashboard' target='_blank'>GitHub</a> |
        <a href='https://docs.ecosystem.ai' target='_blank'>Documentation</a>
        </div>
        """,
        unsafe_allow_html=True
    )

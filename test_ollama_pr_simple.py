#!/usr/bin/env python3
"""
Simple PR Analysis Test with Local Ollama LLM

This script demonstrates PR confidence analysis using your local Ollama instance
for real AI-powered analysis.
"""

import asyncio
import json
import httpx
import time
from datetime import datetime

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"

class OllamaLLMClient:
    """Client for interacting with local Ollama LLM."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate(self, prompt: str, context: str = "", max_tokens: int = 500) -> str:
        """Generate response from Ollama."""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3,
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                print(f"Ollama API error: {response.status_code}")
                return "Error: Unable to generate response from LLM"

        except Exception as e:
            print(f"Ollama connection error: {e}")
            return f"Error: {str(e)}"

async def test_ollama_pr_analysis():
    """Test PR analysis with real Ollama LLM integration."""
    print("🤖 PR CONFIDENCE ANALYSIS WITH LOCAL OLLAMA LLM")
    print("=" * 60)

    # Initialize Ollama client
    ollama_client = OllamaLLMClient()

    # Test data
    pr_content = """
    Title: Implement OAuth2 Authentication Service
    Description: This PR implements OAuth2 authentication for the user service.
    Key changes: Add OAuth2 client configuration, implement token validation middleware,
    add user authentication endpoints, update API documentation.
    Files Changed: src/auth/oauth2_client.py, src/auth/middleware.py
    """

    jira_content = """
    Title: Implement OAuth2 Authentication
    Description: As a user, I want to authenticate using OAuth2 so that I can securely access the API.
    Acceptance Criteria: User can authenticate with OAuth2 provider, API validates OAuth2 tokens,
    Token refresh mechanism implemented, Documentation updated.
    """

    print("📊 Starting Real LLM-Powered PR Analysis")
    print("-" * 40)
    print(f"Model: {OLLAMA_MODEL}")
    print("PR: PR-12345 - OAuth2 Authentication Service")

    total_start_time = time.time()

    try:
        # Step 1: Test Ollama connectivity
        print("\\n1. Testing Ollama Connectivity...")
        test_response = await ollama_client.generate("Hello! Respond with a brief greeting.")
        if "Error" not in test_response:
            print("✅ Ollama connected successfully")
            print(f"   Response: {test_response}")
        else:
            print(f"❌ Ollama connection failed: {test_response}")
            return

        # Step 2: PR-Jira Requirements Alignment Analysis
        print("\\n2. Analyzing PR-Jira Requirements Alignment...")

        prompt = f"""
You are an expert software engineer analyzing a GitHub Pull Request against its requirements.

Pull Request Details:
{pr_content}

Jira Requirements:
{jira_content}

Please analyze how well this PR implements the requirements. Provide a detailed analysis including:
1. Overall alignment score (0-10, where 10 is perfect)
2. Which requirements are fully implemented
3. Which requirements are partially implemented
4. What gaps or missing functionality exist
5. Specific recommendations for improvement

Be specific and technical in your analysis.
"""

        alignment_start = time.time()
        alignment_response = await ollama_client.generate(
            prompt,
            "You are analyzing software requirements alignment between a pull request and its specifications.",
            max_tokens=1000
        )
        alignment_time = time.time() - alignment_start

        print("✅ Requirements alignment analysis completed")
        print(f"   Analysis Time: {alignment_time:.2f}s")

        # Show LLM analysis excerpt
        print("\\n🤖 LLM Analysis (Requirements):")
        print("-" * 30)
        llm_excerpt = alignment_response[:400]
        if len(alignment_response) > 400:
            llm_excerpt += "..."
        print(llm_excerpt)

        # Step 3: Overall Assessment
        print("\\n3. Generating Overall Confidence Assessment...")

        assessment_prompt = f"""
Based on the following PR analysis, provide an overall confidence assessment for PR approval:

Requirements Analysis: {alignment_response[:500]}...

Provide:
1. Overall confidence score (0-100)
2. Confidence level (high/medium/low/critical)
3. Approval recommendation (approve/review_required/reject/hold)
4. Key rationale for your assessment
"""

        confidence_start = time.time()
        confidence_response = await ollama_client.generate(
            assessment_prompt,
            "You are providing a final approval recommendation for a software pull request.",
            max_tokens=600
        )
        confidence_time = time.time() - confidence_start

        print("✅ Confidence assessment completed")
        print(f"   Analysis Time: {confidence_time:.2f}s")

        # Show confidence assessment
        print("\\n🤖 LLM Assessment (Confidence):")
        print("-" * 30)
        confidence_excerpt = confidence_response[:400]
        if len(confidence_response) > 400:
            confidence_excerpt += "..."
        print(confidence_excerpt)

        # Step 4: Extract key metrics from LLM responses
        print("\\n4. Extracting Analysis Metrics...")

        # Simple extraction (in production, you'd use more sophisticated parsing)
        confidence_score = 75  # Default
        confidence_level = "medium"
        approval_rec = "review_required"

        # Look for score in confidence response
        import re
        score_match = re.search(r'(\d+)', confidence_response[:100])
        if score_match:
            confidence_score = int(score_match.group(1))
            if confidence_score >= 80:
                confidence_level = "high"
                approval_rec = "approve"
            elif confidence_score >= 60:
                confidence_level = "medium"
                approval_rec = "review_required"
            else:
                confidence_level = "low"
                approval_rec = "hold"

        total_time = time.time() - total_start_time

        # Create results
        results = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "model": OLLAMA_MODEL,
                "total_time": total_time,
                "pr_id": "PR-12345",
                "analysis_type": "real_llm_powered"
            },
            "llm_responses": {
                "requirements_alignment": alignment_response,
                "confidence_assessment": confidence_response
            },
            "extracted_metrics": {
                "confidence_score": confidence_score,
                "confidence_level": confidence_level,
                "approval_recommendation": approval_rec
            },
            "performance_metrics": {
                "alignment_analysis_time": alignment_time,
                "confidence_assessment_time": confidence_time,
                "total_analysis_time": total_time
            }
        }

        # Save results
        with open("ollama_pr_analysis_simple_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\\n🎉 COMPLETE LLM-POWERED ANALYSIS RESULTS")
        print("=" * 50)

        print("\\n📊 FINAL ANALYSIS SUMMARY:")
        print(f"   Confidence Score: {confidence_score}%")
        print(f"   Confidence Level: {confidence_level.upper()}")
        print(f"   Approval Recommendation: {approval_rec.replace('_', ' ').title()}")
        print(f"   Total Analysis Time: {total_time:.2f}s")

        print("\\n💾 Results saved to: ollama_pr_analysis_simple_results.json")

        print("\\n🎯 SUCCESS HIGHLIGHTS:")
        print("   ✅ Used local Ollama LLM (not simulation)")
        print(f"   ✅ Model: {OLLAMA_MODEL}")
        print("   ✅ Real AI-powered analysis")
        print("   ✅ Context-aware evaluation")
        print("   ✅ Intelligent recommendations")

        return results

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""
    results = await test_ollama_pr_analysis()

    if results:
        print("\\n🚀 SUCCESS: Real LLM-powered PR analysis completed!")
        print("   Your local Ollama instance successfully analyzed the PR with AI.")
    else:
        print("\\n❌ FAILED: PR analysis with Ollama did not complete successfully.")


if __name__ == "__main__":
    asyncio.run(main())

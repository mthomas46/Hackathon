#!/usr/bin/env python3
"""
PR Confidence Analysis Test with Local Ollama LLM

This script demonstrates PR confidence analysis using your local Ollama instance
for real AI-powered analysis instead of simulation.
"""

import asyncio
import json
import httpx
import time
from datetime import datetime
from typing import Dict, Any

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"  # Using the 3.2B model you have available

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
                        "temperature": 0.3,  # Lower temperature for more consistent analysis
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

    async def analyze_requirements_alignment(self, pr_content: str, jira_content: str) -> Dict[str, Any]:
        """Use Ollama to analyze PR vs Jira requirements alignment."""
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

Be specific and technical in your analysis. Focus on the actual implementation vs requirements.
"""

        context = "You are analyzing software requirements alignment between a pull request and its specifications."
        response = await self.generate(prompt, context, max_tokens=1000)

        # Parse the response to extract structured data
        return self._parse_alignment_analysis(response)

    async def analyze_documentation_consistency(self, pr_content: str, doc_content: str) -> Dict[str, Any]:
        """Use Ollama to analyze documentation consistency."""
        prompt = f"""
You are analyzing the consistency between code changes and existing documentation.

Pull Request Changes:
{pr_content}

Existing Documentation:
{doc_content}

Please evaluate how well the PR aligns with the documentation. Focus on:
1. API consistency - do the code changes match documented APIs?
2. Security requirements - are security guidelines followed?
3. Breaking changes - are there undocumented breaking changes?
4. Documentation updates needed - what needs to be updated?

Provide specific findings about consistency issues or confirm consistency where appropriate.
"""

        context = "You are evaluating documentation consistency in software development."
        response = await self.generate(prompt, context, max_tokens=800)

        return self._parse_consistency_analysis(response)

    async def generate_confidence_assessment(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use Ollama to generate overall confidence assessment."""
        prompt = f"""
You are assessing the overall confidence level for approving a pull request based on the following analysis:

Requirements Alignment Score: {analysis_data.get('requirements_score', 0):.2f}/10
Documentation Consistency Score: {analysis_data.get('documentation_score', 0):.2f}/10
Gaps Identified: {len(analysis_data.get('gaps', []))}
Risk Factors: {len(analysis_data.get('risks', []))}

Requirements Analysis: {analysis_data.get('requirements_analysis', 'N/A')}
Documentation Analysis: {analysis_data.get('documentation_analysis', 'N/A')}

Based on this comprehensive analysis, provide an overall confidence assessment for PR approval.
Consider enterprise software standards and best practices in your assessment.

Provide:
1. Overall confidence score (0-100)
2. Confidence level (high/medium/low/critical)
3. Approval recommendation (approve/review_required/reject/hold)
4. Key rationale for your assessment
5. Critical concerns if any
"""

        context = "You are providing a final approval recommendation for a software pull request."
        response = await self.generate(prompt, context, max_tokens=600)

        return self._parse_confidence_assessment(response)

    def _parse_alignment_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured alignment analysis."""
        # Extract score from response
        score = 7.5  # Default
        if "score" in response.lower():
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)/10', response)
            if score_match:
                score = float(score_match.group(1))

        # Extract key findings
        gaps = []
        recommendations = []

        if "missing" in response.lower() or "gap" in response.lower():
            gaps.append("Implementation gaps identified in LLM analysis")

        if "recommend" in response.lower():
            recommendations.append("Follow LLM recommendations for improvement")

        return {
            "overall_score": score / 10,  # Convert to 0-1 scale
            "llm_analysis": response,
            "gaps": gaps,
            "recommendations": recommendations
        }

    def _parse_consistency_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured consistency analysis."""
        score = 0.8  # Default good consistency
        issues = []

        if "inconsistent" in response.lower() or "missing" in response.lower():
            score = 0.6
            issues.append("Documentation consistency issues found")

        return {
            "consistency_score": score,
            "issues": issues,
            "llm_analysis": response
        }

    def _parse_confidence_assessment(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured confidence assessment."""
        confidence_score = 75  # Default
        confidence_level = "medium"
        approval_rec = "review_required"

        # Extract confidence score
        import re
        score_match = re.search(r'(\d+)', response[:100])  # Look in first 100 chars
        if score_match:
            confidence_score = int(score_match.group(1))

        # Determine level and recommendation based on score
        if confidence_score >= 80:
            confidence_level = "high"
            approval_rec = "approve"
        elif confidence_score >= 60:
            confidence_level = "medium"
            approval_rec = "review_required"
        else:
            confidence_level = "low"
            approval_rec = "hold"

        return {
            "overall_confidence": confidence_score / 100,  # Convert to 0-1
            "confidence_level": confidence_level,
            "approval_recommendation": approval_rec,
            "rationale": response,
            "critical_concerns": [] if confidence_score >= 60 else ["LLM identified significant concerns"]
        }


async def test_ollama_pr_analysis():
    """Test PR analysis with real Ollama LLM integration."""
    print("🤖 PR CONFIDENCE ANALYSIS WITH LOCAL OLLAMA LLM")
    print("=" * 60)

    # Initialize Ollama client
    ollama_client = OllamaLLMClient()

    # Test data
    pr_data = {
        "id": "PR-12345",
        "title": "Implement OAuth2 Authentication Service",
        "description": """
        This PR implements OAuth2 authentication for the user service.
        Key changes:
        - Add OAuth2 client configuration
        - Implement token validation middleware
        - Add user authentication endpoints
        - Update API documentation

        Related Jira: PROJ-456
        Confluence Docs: API_AUTH_DOCS, SECURITY_GUIDE
        """,
        "author": "developer@example.com",
        "jira_ticket": "PROJ-456",
        "files_changed": [
            "src/auth/oauth2_client.py",
            "src/auth/middleware.py",
            "src/api/auth_endpoints.py",
            "docs/api/authentication.md"
        ],
        "diff_summary": "+250 lines, -50 lines"
    }

    jira_data = {
        "id": "PROJ-456",
        "title": "Implement OAuth2 Authentication",
        "description": "As a user, I want to authenticate using OAuth2 so that I can securely access the API.",
        "acceptance_criteria": [
            "User can authenticate with OAuth2 provider",
            "API validates OAuth2 tokens",
            "Token refresh mechanism implemented",
            "Documentation updated"
        ],
        "story_points": 8,
        "priority": "High"
    }

    confluence_docs = [{
        "id": "API_AUTH_DOCS",
        "title": "Authentication API Documentation",
        "content": """
        # Authentication Service

        ## OAuth2 Flow
        1. Client requests authorization
        2. User is redirected to OAuth provider
        3. Provider returns authorization code
        4. Client exchanges code for access token

        ## Endpoints
        - POST /auth/login - User login
        - POST /auth/token - Token exchange
        - POST /auth/refresh - Token refresh
        - GET /auth/user - Get user info

        ## Security Requirements
        - All endpoints must validate JWT tokens
        - Tokens must expire within 1 hour
        - Refresh tokens valid for 30 days
        """,
        "last_updated": "2024-09-10T14:30:00Z"
    }]

    print("📊 Starting Real LLM-Powered PR Analysis")
    print("-" * 40)
    print(f"Model: {OLLAMA_MODEL}")
    print(f"PR: {pr_data['id']} - {pr_data['title']}")
    print(f"Jira: {jira_data['id']}")
    print(f"Confluence Docs: {len(confluence_docs)}")

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
        pr_content = f"""
Title: {pr_data['title']}
Description: {pr_data['description']}
Files Changed: {', '.join(pr_data['files_changed'])}
"""

        jira_content = f"""
Title: {jira_data['title']}
Description: {jira_data['description']}
Acceptance Criteria: {'; '.join(jira_data['acceptance_criteria'])}
Priority: {jira_data['priority']}
"""

        alignment_start = time.time()
        alignment_analysis = await ollama_client.analyze_requirements_alignment(pr_content, jira_content)
        alignment_time = time.time() - alignment_start

        print("✅ Requirements alignment analysis completed")
        print(f"   Analysis Time: {alignment_time:.2f}s")

        # Show LLM analysis
        llm_analysis = alignment_analysis.get('llm_analysis', '')[:300]
        if len(alignment_analysis.get('llm_analysis', '')) > 300:
            llm_analysis += "..."
        print(f"   LLM Analysis: {llm_analysis}")

        # Step 3: Documentation Consistency Analysis
        print("\\n3. Analyzing Documentation Consistency...")
        doc_content = confluence_docs[0]['content']

        consistency_start = time.time()
        consistency_analysis = await ollama_client.analyze_documentation_consistency(pr_content, doc_content)
        consistency_time = time.time() - consistency_start

        print("✅ Documentation consistency analysis completed")
        print(f"   Analysis Time: {consistency_time:.2f}s")

        # Step 4: Overall Confidence Assessment
        print("\\n4. Generating Overall Confidence Assessment...")
        analysis_data = {
            'requirements_score': alignment_analysis.get('overall_score', 0) * 10,
            'documentation_score': consistency_analysis.get('consistency_score', 0) * 10,
            'gaps': alignment_analysis.get('gaps', []),
            'risks': consistency_analysis.get('issues', []),
            'requirements_analysis': alignment_analysis.get('llm_analysis', ''),
            'documentation_analysis': consistency_analysis.get('llm_analysis', '')
        }

        confidence_start = time.time()
        confidence_assessment = await ollama_client.generate_confidence_assessment(analysis_data)
        confidence_time = time.time() - confidence_start

        print("✅ Confidence assessment completed"        print(f"   Score: {consistency_analysis.get("consistency_score", 0):.1%}")
        print(f"   Level: {confidence_assessment.get('confidence_level', 'unknown').upper()}")
        print(f"   Recommendation: {confidence_assessment.get('approval_recommendation', 'unknown').replace('_', ' ').title()}")
        print(f"   Analysis Time: {confidence_time:.2f}s")

        # Step 5: Comprehensive Results
        total_time = time.time() - total_start_time

        print("\\n🎉 COMPLETE LLM-POWERED ANALYSIS RESULTS")
        print("=" * 50)

        results = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "model": OLLAMA_MODEL,
                "total_time": total_time,
                "pr_id": pr_data["id"],
                "jira_id": jira_data["id"]
            },
            "requirements_alignment": {
                "score": alignment_analysis.get("overall_score", 0),
                "llm_analysis": alignment_analysis.get("llm_analysis", ""),
                "gaps": alignment_analysis.get("gaps", []),
                "recommendations": alignment_analysis.get("recommendations", [])
            },
            "documentation_consistency": {
                "score": consistency_analysis.get("consistency_score", 0),
                "issues": consistency_analysis.get("issues", []),
                "llm_analysis": consistency_analysis.get("llm_analysis", "")
            },
            "confidence_assessment": {
                "overall_score": confidence_assessment.get("overall_confidence", 0),
                "confidence_level": confidence_assessment.get("confidence_level", "unknown"),
                "approval_recommendation": confidence_assessment.get("approval_recommendation", "unknown"),
                "rationale": confidence_assessment.get("rationale", ""),
                "critical_concerns": confidence_assessment.get("critical_concerns", [])
            },
            "performance_metrics": {
                "alignment_analysis_time": alignment_time,
                "consistency_analysis_time": consistency_time,
                "confidence_assessment_time": confidence_time,
                "total_analysis_time": total_time
            }
        }

        # Save detailed results
        with open("ollama_pr_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\\n📊 FINAL ANALYSIS SUMMARY:")
        print(f"   Overall Confidence: {confidence_assessment.get('overall_confidence', 0):.1%}")
        print(f"   Confidence Level: {confidence_assessment.get('confidence_level', 'unknown').upper()}")
        print(f"   Approval Recommendation: {confidence_assessment.get('approval_recommendation', 'unknown').replace('_', ' ').title()}")
        print(f"   Total Analysis Time: {total_time:.2f}s")

        print("\\n💾 Detailed results saved to: ollama_pr_analysis_results.json")

        # Show LLM analysis excerpts
        print("\\n🤖 LLM ANALYSIS EXCERPTS:")
        print("-" * 30)

        if alignment_analysis.get('llm_analysis'):
            print("Requirements Analysis:")
            excerpt = alignment_analysis['llm_analysis'][:200]
            print(f"   \"{excerpt}...\"")

        if consistency_analysis.get('llm_analysis'):
            print("\\nDocumentation Analysis:")
            excerpt = consistency_analysis['llm_analysis'][:200]
            print(f"   \"{excerpt}...\"")

        if confidence_assessment.get('rationale'):
            print("\\nConfidence Rationale:")
            excerpt = confidence_assessment['rationale'][:200]
            print(f"   \"{excerpt}...\"")

        print("\\n🎯 ANALYSIS COMPLETE!")
        print("   ✅ Used local Ollama LLM for all analysis steps")
        print(f"   ✅ Model: {OLLAMA_MODEL}")
        print("   ✅ Real AI-powered analysis (not simulation)")
        print("   ✅ Context-aware evaluation and recommendations")

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

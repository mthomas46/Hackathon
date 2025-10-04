"""
Unit tests for Workflow F: SME Synthesis and Collaboration Mapping

Tests SME identification, expertise scoring, collaboration graph building,
and expertise mapping functionality.
"""

import pytest
from typing import Dict, Any
import sys
import os

# Add services directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../services')))

try:
    from services.project_planning_service.domain.services.workflow_f_user_intelligence import (
        UserIntelligenceWorkflow,
        UserExtraction,
        SubjectMatterExpert
    )
except ImportError:
    # Try alternative import path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "workflow_f_user_intelligence",
        os.path.join(os.path.dirname(__file__), "../../../services/project-planning-service/domain/services/workflow_f_user_intelligence.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    UserIntelligenceWorkflow = module.UserIntelligenceWorkflow
    UserExtraction = module.UserExtraction
    SubjectMatterExpert = module.SubjectMatterExpert


class TestExpertiseScoreCalculation:
    """Test expertise score calculation algorithm."""
    
    def test_score_with_created_documents(self):
        """Test scoring user with created documents (strong signal)."""
        workflow = UserIntelligenceWorkflow()
        
        extraction = UserExtraction(
            username="alice.cooper",
            documents_created=["doc1", "doc2", "doc3", "doc4", "doc5"],
            documents_updated=[],
            documents_commented=[]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        # 5 created * 0.3 = 1.5, normalized to 1.0
        assert score > 0
        assert score <= 1.0
        # Should have high score due to created documents
        assert score >= 0.15  # At least 1.5/10 = 0.15
    
    def test_score_with_updated_documents(self):
        """Test scoring user with updated documents (medium signal)."""
        workflow = UserIntelligenceWorkflow()
        
        extraction = UserExtraction(
            username="bob.martin",
            documents_created=[],
            documents_updated=["doc1", "doc2", "doc3"],
            documents_commented=[]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        # 3 updated * 0.2 = 0.6 / 10 = 0.06
        assert score > 0
        assert score >= 0.06
    
    def test_score_with_commented_documents(self):
        """Test scoring user with commented documents (weak signal)."""
        workflow = UserIntelligenceWorkflow()
        
        extraction = UserExtraction(
            username="charlie.davis",
            documents_created=[],
            documents_updated=[],
            documents_commented=["doc1", "doc2"]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        # 2 commented * 0.1 = 0.2 / 10 = 0.02
        assert score > 0
        assert score >= 0.02
    
    def test_score_with_topics_and_skills(self):
        """Test that topics and skills contribute to score."""
        workflow = UserIntelligenceWorkflow()
        
        extraction = UserExtraction(
            username="diana.evans",
            documents_created=["doc1"],
            topics=["Python", "Backend", "APIs"],
            skills=["Python Development", "API Design"]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        # Should have bonus from topics and skills
        # 1 created (0.3) + 3 topics (0.15) + 2 skills (0.1) = 0.55 / 10 = 0.055+
        assert score > 0.05
    
    def test_score_with_collaborators(self):
        """Test that collaborators contribute to score."""
        workflow = UserIntelligenceWorkflow()
        
        extraction = UserExtraction(
            username="eve.foster",
            documents_created=["doc1"],
            collaborators=["user1", "user2", "user3"]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        # Should have bonus from collaboration
        # 1 created (0.3) + 3 collaborators (0.3) = 0.6 / 10 = 0.06
        assert score > 0.05
    
    def test_score_normalized_to_max_1(self):
        """Test that score is normalized to maximum of 1.0."""
        workflow = UserIntelligenceWorkflow()
        
        # Create extraction with very high values
        extraction = UserExtraction(
            username="power.user",
            documents_created=["d" + str(i) for i in range(50)],  # 50 documents
            documents_updated=["u" + str(i) for i in range(20)],
            documents_commented=["c" + str(i) for i in range(30)],
            topics=["t" + str(i) for i in range(20)],
            skills=["s" + str(i) for i in range(10)],
            collaborators=["u" + str(i) for i in range(15)]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        # Score should be capped at 1.0
        assert score == 1.0
    
    def test_score_zero_for_no_activity(self):
        """Test that score is 0 for user with no activity."""
        workflow = UserIntelligenceWorkflow()
        
        extraction = UserExtraction(
            username="inactive.user",
            documents_created=[],
            documents_updated=[],
            documents_commented=[]
        )
        
        score = workflow._calculate_expertise_score(extraction)
        
        assert score == 0.0


class TestSMESynthesis:
    """Test subject matter expert synthesis."""
    
    def test_synthesize_basic_sme(self, sample_user_extractions):
        """Test synthesizing SMEs from user extractions."""
        workflow = UserIntelligenceWorkflow()
        workflow.user_extractions = sample_user_extractions
        
        smes = workflow.synthesize_subject_matter_experts(
            min_interactions=2
        )
        
        # Should have identified SMEs
        assert len(smes) > 0
        
        # Each SME should have required fields
        for sme in smes:
            assert isinstance(sme, SubjectMatterExpert)
            assert sme.username
            assert sme.display_name
            assert sme.area_of_expertise
            assert 0 <= sme.confidence <= 1.0
            assert len(sme.evidence) > 0
            assert sme.contact_priority in ["high", "medium", "low"]
    
    def test_synthesize_with_min_interactions_filter(self):
        """Test that min_interactions filters out low-activity users."""
        workflow = UserIntelligenceWorkflow()
        
        # Add users with different interaction counts
        workflow.user_extractions = {
            "high.activity": UserExtraction(
                username="high.activity",
                documents_created=["d1", "d2", "d3", "d4", "d5"],
                topics=["Python", "Backend"],  # Need topics for SME generation
                total_interactions=5
            ),
            "low.activity": UserExtraction(
                username="low.activity",
                documents_created=["d1"],
                topics=["Python"],  # Need topics for SME generation
                total_interactions=1
            )
        }
        
        smes = workflow.synthesize_subject_matter_experts(
            min_interactions=3  # Require at least 3 interactions
        )
        
        # Should only include high.activity user
        sme_usernames = [sme.username for sme in smes]
        assert "high.activity" in sme_usernames
        assert "low.activity" not in sme_usernames
    
    def test_synthesize_identifies_team_members(self, sample_team_members):
        """Test that SME synthesis identifies team members."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "sarah.chen": UserExtraction(
                username="sarah.chen",
                display_name="Sarah Chen",
                documents_created=["d1", "d2", "d3"],
                topics=["Python"],
                total_interactions=3
            ),
            "external.expert": UserExtraction(
                username="external.expert",
                display_name="External Expert",
                documents_created=["d4", "d5"],
                topics=["Python"],
                total_interactions=2
            )
        }
        
        smes = workflow.synthesize_subject_matter_experts(
            min_interactions=2,
            team_members=sample_team_members
        )
        
        # Check team member flag
        for sme in smes:
            if sme.username == "sarah.chen" or sme.display_name == "Sarah Chen":
                assert sme.is_team_member == True
            elif sme.username == "external.expert":
                assert sme.is_team_member == False
    
    def test_synthesize_creates_expertise_areas(self):
        """Test that SMEs are created for different expertise areas."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "python.expert": UserExtraction(
                username="python.expert",
                documents_created=["d1", "d2", "d3"],
                topics=["Python", "Backend"],
                total_interactions=3
            )
        }
        
        smes = workflow.synthesize_subject_matter_experts(min_interactions=2)
        
        # Should create SMEs for topics
        assert len(smes) > 0
        
        # Check expertise areas match topics
        expertise_areas = [sme.area_of_expertise for sme in smes]
        assert any("Python" in area for area in expertise_areas)
    
    def test_synthesize_includes_evidence(self):
        """Test that SMEs include evidence for their expertise."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "expert.user": UserExtraction(
                username="expert.user",
                documents_created=["d1", "d2"],
                documents_commented=["d3", "d4", "d5"],
                topics=["Python", "APIs"],
                total_interactions=5
            )
        }
        
        smes = workflow.synthesize_subject_matter_experts(min_interactions=2)
        
        assert len(smes) > 0
        
        for sme in smes:
            # Should have evidence
            assert len(sme.evidence) > 0
            # Evidence should mention documents and topics
            evidence_text = " ".join(sme.evidence)
            assert "documents" in evidence_text.lower() or "Topics" in evidence_text
    
    def test_synthesize_assigns_contact_priority(self):
        """Test that contact priority is assigned based on expertise score."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "high.expert": UserExtraction(
                username="high.expert",
                documents_created=["d" + str(i) for i in range(10)],
                topics=["Python", "Backend", "APIs"],
                total_interactions=10
            ),
            "medium.expert": UserExtraction(
                username="medium.expert",
                documents_created=["d1", "d2", "d3"],
                topics=["Python"],
                total_interactions=3
            )
        }
        
        smes = workflow.synthesize_subject_matter_experts(min_interactions=2)
        
        # Should have different priority levels
        priorities = [sme.contact_priority for sme in smes]
        assert "high" in priorities or "medium" in priorities
    
    def test_synthesize_sorted_by_confidence(self):
        """Test that SMEs are sorted by confidence score."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "expert1": UserExtraction(
                username="expert1",
                documents_created=["d" + str(i) for i in range(10)],
                total_interactions=10
            ),
            "expert2": UserExtraction(
                username="expert2",
                documents_created=["d1", "d2"],
                total_interactions=2
            ),
            "expert3": UserExtraction(
                username="expert3",
                documents_created=["d" + str(i) for i in range(5)],
                total_interactions=5
            )
        }
        
        smes = workflow.synthesize_subject_matter_experts(min_interactions=2)
        
        # Should be sorted by confidence (descending)
        if len(smes) > 1:
            for i in range(len(smes) - 1):
                assert smes[i].confidence >= smes[i + 1].confidence


class TestCollaborationGraphBuilding:
    """Test collaboration graph construction."""
    
    def test_build_empty_graph(self):
        """Test building graph with no users."""
        workflow = UserIntelligenceWorkflow()
        
        graph = workflow.build_collaboration_graph()
        
        assert isinstance(graph, dict)
        assert len(graph) == 0
    
    def test_build_graph_single_user(self):
        """Test building graph with single user."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "solo.user": UserExtraction(
                username="solo.user",
                documents_created=["doc1"]
            )
        }
        
        graph = workflow.build_collaboration_graph()
        
        # Should have entry for user
        assert "solo.user" in graph
        # But no collaborators (worked alone)
        assert len(graph["solo.user"]) == 0
    
    def test_build_graph_identifies_collaborators(self):
        """Test that users who work on same documents are identified as collaborators."""
        workflow = UserIntelligenceWorkflow()
        
        # Create users who worked on same document
        workflow.user_extractions = {
            "alice": UserExtraction(
                username="alice",
                documents_created=["doc1"]
            ),
            "bob": UserExtraction(
                username="bob",
                documents_commented=["doc1"]  # Commented on alice's doc
            )
        }
        
        graph = workflow.build_collaboration_graph()
        
        # Alice and Bob should be collaborators
        assert "bob" in graph["alice"]
        assert "alice" in graph["bob"]
    
    def test_build_graph_multiple_documents(self):
        """Test collaboration across multiple shared documents."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "user1": UserExtraction(
                username="user1",
                documents_created=["doc1", "doc2"]
            ),
            "user2": UserExtraction(
                username="user2",
                documents_created=["doc1"],  # Shared doc1
                documents_updated=["doc2"]   # Shared doc2
            )
        }
        
        graph = workflow.build_collaboration_graph()
        
        # Should be collaborators due to shared documents
        assert "user2" in graph["user1"]
        assert "user1" in graph["user2"]
    
    def test_build_graph_excludes_self(self):
        """Test that users are not their own collaborators."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "alice": UserExtraction(
                username="alice",
                documents_created=["doc1"],
                documents_updated=["doc1"]  # Same user, same doc
            )
        }
        
        graph = workflow.build_collaboration_graph()
        
        # Should not include self as collaborator
        assert "alice" not in graph["alice"]
    
    def test_build_graph_transitive_relationships(self):
        """Test that collaboration graph captures transitive relationships."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "alice": UserExtraction(
                username="alice",
                documents_created=["doc1"]
            ),
            "bob": UserExtraction(
                username="bob",
                documents_created=["doc1", "doc2"]  # Shared doc1 with alice
            ),
            "charlie": UserExtraction(
                username="charlie",
                documents_created=["doc2"]  # Shared doc2 with bob
            )
        }
        
        graph = workflow.build_collaboration_graph()
        
        # Alice and Bob collaborated
        assert "bob" in graph["alice"]
        # Bob and Charlie collaborated
        assert "charlie" in graph["bob"]
        # But Alice and Charlie didn't directly collaborate (no shared docs)
        assert "charlie" not in graph["alice"]
    
    def test_build_graph_updates_extraction_collaborators(self):
        """Test that building graph updates UserExtraction.collaborators."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "alice": UserExtraction(
                username="alice",
                documents_created=["doc1"]
            ),
            "bob": UserExtraction(
                username="bob",
                documents_created=["doc1"]
            )
        }
        
        workflow.build_collaboration_graph()
        
        # Should update collaborators field
        assert "bob" in workflow.user_extractions["alice"].collaborators
        assert "alice" in workflow.user_extractions["bob"].collaborators


class TestExpertiseMapBuilding:
    """Test expertise map construction."""
    
    def test_build_empty_expertise_map(self):
        """Test building map with no users."""
        workflow = UserIntelligenceWorkflow()
        
        expertise_map = workflow.build_expertise_map()
        
        assert isinstance(expertise_map, dict)
        assert len(expertise_map) == 0
    
    def test_build_map_with_topics(self):
        """Test mapping topics to experts."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "python.expert": UserExtraction(
                username="python.expert",
                topics=["Python", "Backend"]
            )
        }
        
        expertise_map = workflow.build_expertise_map()
        
        # Should map topics to user
        assert "Python" in expertise_map
        assert "python.expert" in expertise_map["Python"]
        assert "Backend" in expertise_map
        assert "python.expert" in expertise_map["Backend"]
    
    def test_build_map_with_skills(self):
        """Test mapping skills to experts."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "skilled.user": UserExtraction(
                username="skilled.user",
                skills=["API Design", "Database Design"]
            )
        }
        
        expertise_map = workflow.build_expertise_map()
        
        # Should map skills to user
        assert "API Design" in expertise_map
        assert "skilled.user" in expertise_map["API Design"]
    
    def test_build_map_multiple_experts_per_topic(self):
        """Test that multiple experts can be mapped to same topic."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "expert1": UserExtraction(
                username="expert1",
                topics=["Python"]
            ),
            "expert2": UserExtraction(
                username="expert2",
                topics=["Python", "Go"]
            )
        }
        
        expertise_map = workflow.build_expertise_map()
        
        # Both experts should be mapped to Python
        assert "Python" in expertise_map
        assert "expert1" in expertise_map["Python"]
        assert "expert2" in expertise_map["Python"]
        assert len(expertise_map["Python"]) == 2
    
    def test_build_map_deduplicates_users(self):
        """Test that users aren't duplicated in expertise map."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "user1": UserExtraction(
                username="user1",
                topics=["Python"],
                skills=["Python"]  # Duplicate expertise area
            )
        }
        
        expertise_map = workflow.build_expertise_map()
        
        # Should only appear once
        if "Python" in expertise_map:
            assert expertise_map["Python"].count("user1") == 1


class TestWorkflowFExecution:
    """Test full Workflow F execution."""
    
    def test_execute_builds_all_structures(self, sample_github_pr, sample_jira_ticket):
        """Test that execute builds all required data structures."""
        workflow = UserIntelligenceWorkflow()
        
        result = workflow.execute(
            jira_tickets=[sample_jira_ticket],
            confluence_docs=[],
            github_prs=[sample_github_pr]
        )
        
        # Should have extracted users
        assert result.total_users_extracted > 0
        assert len(result.extracted_users) > 0
        
        # Should have built collaboration graph
        assert isinstance(result.collaboration_graph, dict)
        
        # Should have built expertise map
        assert isinstance(result.expertise_map, dict)
        
        # Should have potential contacts
        assert isinstance(result.potential_contacts, dict)
        
        # Should have SMEs
        assert isinstance(result.subject_matter_experts, list)
    
    def test_execute_with_team_members(self, sample_github_pr, sample_team_members):
        """Test execute with team member filtering."""
        workflow = UserIntelligenceWorkflow()
        
        result = workflow.execute(
            jira_tickets=[],
            confluence_docs=[],
            github_prs=[sample_github_pr],
            team_members=sample_team_members
        )
        
        # Should identify team members in SMEs
        for sme in result.subject_matter_experts:
            # is_team_member should be set
            assert hasattr(sme, 'is_team_member')
            assert isinstance(sme.is_team_member, bool)


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestSMEEdgeCases:
    """Test edge cases in SME synthesis."""
    
    def test_synthesize_with_no_topics(self):
        """Test SME synthesis when users have no topics."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "user1": UserExtraction(
                username="user1",
                documents_created=["d1", "d2", "d3"],
                topics=[],  # No topics
                total_interactions=3
            )
        }
        
        # Should not crash
        smes = workflow.synthesize_subject_matter_experts(min_interactions=2)
        
        # May or may not produce SMEs, but shouldn't error
        assert isinstance(smes, list)
    
    def test_synthesize_with_very_high_min_interactions(self):
        """Test with unreasonably high minimum interactions."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "user1": UserExtraction(
                username="user1",
                documents_created=["d1"],
                total_interactions=1
            )
        }
        
        # Set impossibly high threshold
        smes = workflow.synthesize_subject_matter_experts(min_interactions=1000)
        
        # Should return empty list (no users meet threshold)
        assert len(smes) == 0
    
    def test_collaboration_graph_with_no_shared_documents(self):
        """Test collaboration graph when no users share documents."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "user1": UserExtraction(
                username="user1",
                documents_created=["doc1"]
            ),
            "user2": UserExtraction(
                username="user2",
                documents_created=["doc2"]  # Different document
            )
        }
        
        graph = workflow.build_collaboration_graph()
        
        # Both users should be in graph but with no collaborators
        assert "user1" in graph
        assert "user2" in graph
        assert len(graph["user1"]) == 0
        assert len(graph["user2"]) == 0
    
    def test_expertise_map_with_empty_topics_and_skills(self):
        """Test expertise map when users have no topics or skills."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.user_extractions = {
            "user1": UserExtraction(
                username="user1",
                topics=[],
                skills=[]
            )
        }
        
        expertise_map = workflow.build_expertise_map()
        
        # Should be empty (no expertise to map)
        assert len(expertise_map) == 0


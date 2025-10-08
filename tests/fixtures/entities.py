"""
Entity and relationship fixtures for testing corpus analysis.
"""
from typing import Dict, List, Tuple, Any


def create_mock_entity(
    text: str,
    entity_type: str = "PERSON",
    frequency: int = 5
) -> Tuple[str, int]:
    """
    Create a mock entity.
    
    Args:
        text: Entity text
        entity_type: Entity type (PERSON, ORG, LOCATION, etc.)
        frequency: Occurrence frequency
    
    Returns:
        Tuple of (text, frequency)
    """
    return (text, frequency)


def create_mock_relationship(
    entity1: str,
    entity2: str,
    weight: int = 3
) -> Tuple[str, str, int]:
    """
    Create a mock relationship.
    
    Args:
        entity1: First entity
        entity2: Second entity
        weight: Relationship strength
    
    Returns:
        Tuple of (entity1, entity2, weight)
    """
    return (entity1, entity2, weight)


# Sample entities by type
SAMPLE_ENTITIES = {
    'PERSON': [
        create_mock_entity("John Smith", "PERSON", 10),
        create_mock_entity("Jane Doe", "PERSON", 8),
        create_mock_entity("Dr. Alice Johnson", "PERSON", 6),
        create_mock_entity("Bob Wilson", "PERSON", 5),
    ],
    'ORGANIZATION': [
        create_mock_entity("OpenAI", "ORGANIZATION", 12),
        create_mock_entity("Google", "ORGANIZATION", 10),
        create_mock_entity("Microsoft", "ORGANIZATION", 9),
        create_mock_entity("Meta", "ORGANIZATION", 7),
    ],
    'LOCATION': [
        create_mock_entity("San Francisco", "LOCATION", 8),
        create_mock_entity("New York", "LOCATION", 7),
        create_mock_entity("London", "LOCATION", 6),
        create_mock_entity("Tokyo", "LOCATION", 5),
    ],
    'TECHNOLOGY': [
        create_mock_entity("Machine Learning", "TECHNOLOGY", 15),
        create_mock_entity("Neural Networks", "TECHNOLOGY", 12),
        create_mock_entity("Deep Learning", "TECHNOLOGY", 10),
        create_mock_entity("Natural Language Processing", "TECHNOLOGY", 9),
    ]
}


# Sample relationships
SAMPLE_RELATIONSHIPS = [
    # People and organizations
    create_mock_relationship("John Smith", "OpenAI", 8),
    create_mock_relationship("Jane Doe", "Google", 7),
    create_mock_relationship("Dr. Alice Johnson", "Microsoft", 6),
    
    # Organizations and technologies
    create_mock_relationship("OpenAI", "Machine Learning", 10),
    create_mock_relationship("Google", "Neural Networks", 9),
    create_mock_relationship("Microsoft", "Deep Learning", 8),
    
    # Technologies and concepts
    create_mock_relationship("Machine Learning", "Neural Networks", 12),
    create_mock_relationship("Deep Learning", "Neural Networks", 11),
    create_mock_relationship("Machine Learning", "Natural Language Processing", 9),
    
    # Locations and organizations
    create_mock_relationship("San Francisco", "OpenAI", 5),
    create_mock_relationship("San Francisco", "Google", 4),
    create_mock_relationship("New York", "Microsoft", 4),
]


def create_entities_by_type(custom_entities: Dict[str, List[Tuple[str, int]]] = None) -> Dict[str, List[Tuple[str, int]]]:
    """
    Create a complete entities_by_type dictionary.
    
    Args:
        custom_entities: Optional custom entity dictionary
    
    Returns:
        Dictionary mapping entity types to lists of (text, frequency) tuples
    """
    if custom_entities:
        return custom_entities
    
    return SAMPLE_ENTITIES.copy()


def create_relationship_list(custom_relationships: List[Tuple[str, str, int]] = None) -> List[Tuple[str, str, int]]:
    """
    Create a relationship list.
    
    Args:
        custom_relationships: Optional custom relationship list
    
    Returns:
        List of (entity1, entity2, weight) tuples
    """
    if custom_relationships:
        return custom_relationships
    
    return SAMPLE_RELATIONSHIPS.copy()


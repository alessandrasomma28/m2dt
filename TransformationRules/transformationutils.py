import random
import string
import pandas as pd

def generateId(existingIds: set, length: int = 10) -> str:
    """
    Generate a unique alphanumeric ID of specified length.

    Args:
        existingIds (set): A set of existing IDs to ensure uniqueness.
        length (int): Length of the generated ID. Default is 10.

    Returns:
        str: A unique alphanumeric ID not present in existingIds.
    """
    while True:
        # Generate a random alphanumeric string of the specified length
        newId = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        # Check if the generated ID is unique within existingIds
        if newId not in existingIds:
            existingIds.add(newId)  # Track the new ID to maintain uniqueness
            return newId  # Return the unique ID
def getIdLength(classesDf: pd.DataFrame) -> int:
    """
    Get the length of the longest existing class ID to ensure new IDs follow the same pattern.

    Args:
        classesDf (pd.DataFrame): DataFrame of classes.

    Returns:
        int: Length of the longest class ID.
    """
    return classesDf['Class ID'].apply(len).max()
def getExistingIds(classesDf: pd.DataFrame) -> set:
    """
    Get the set of existing class IDs to ensure uniqueness.

    Args:
        classesDf (pd.DataFrame): DataFrame of classes.

    Returns:
        set: Set of existing class IDs.
    """
    # Return an empty set if the DataFrame is empty
    if classesDf.empty:
        return set()

    return set(classesDf['Class ID'])
def findGeneralizationChildClasses(relationsDf: pd.DataFrame, parentClassId: str) -> pd.DataFrame:
    """
    Find all child classes of a given 'From Class ID' in generalization relationships.

    Args:
        relationsDf (pd.DataFrame): DataFrame of relationships.
        parentClassId (str): The ID of the parent class in the generalization relationship.

    Returns:
        pd.DataFrame: DataFrame of child classes in the generalization relationship.
    """
    return relationsDf[(relationsDf['Relationship Type'] == 'Generalization') &
                       (relationsDf['From Class ID'] == parentClassId)]
def findClassId(dfClasses: pd.DataFrame, className: str) -> str:
    """
    Find the class ID of a class by its name.

    Args:
        dfClasses (pd.DataFrame): DataFrame of classes.
        className (str): The name of the class.

    Returns:
        str: The class ID or None if not found.
    """
    classId = dfClasses[dfClasses['Class Name'] == className]['Class ID'].values
    return classId[0] if len(classId) > 0 else None
def findRelatedRelationships(relationsDf: pd.DataFrame, classId: str) -> pd.DataFrame:
    """
    Find relationships (associations, aggregations, compositions) involving a class by its ID.

    Args:
        relationsDf (pd.DataFrame): DataFrame of relationships.
        classId (str): ID of the class for which relationships should be found.

    Returns:
        pd.DataFrame: DataFrame of found relationships.
    """
    # Find the relationships involving the class
    relatedRelationships = relationsDf[
        (relationsDf['From Class ID'] == classId) | (relationsDf['To Class ID'] == classId)
        ]

    # If the result is a list, convert it to a DataFrame (this check may be unnecessary)
    if isinstance(relatedRelationships, list):
        relatedRelationships = pd.DataFrame(relatedRelationships)

    return relatedRelationships

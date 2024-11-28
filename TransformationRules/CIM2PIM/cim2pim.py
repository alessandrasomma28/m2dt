from TransformationRules.transformationutils import generateId, getIdLength, getExistingIds, \
    findGeneralizationChildClasses, findClassId, findRelatedRelationships, findClassesByPartialName
import pandas as pd
from TransformationRules.constants import (CIM_REAL_TWIN_CLASS_NAME, PHYSICAL_ENTITY_CLASS_NAME,
                                           TEMPORAL_ENTITY_CLASS_NAME, SENSOR_ENTITY_CLASS_NAME,
                                           ACTUATOR_ENTITY_CLASS_NAME, PIM_REAL_TWIN_CLASS_NAME)


def cim2pimTransformation(cimClasses, cimRelations):
    pimRelations = pd.DataFrame(
        columns=["Relationship Type", "From Class ID", "From Class Name", "To Class ID", "To Class Name",
                 "Aggregation"])
    pimClasses = {}

    # RULE 1. mapToPhysicalTwin
    pimClasses = mapToPhysicalTwin(cimClasses, cimRelations, CIM_REAL_TWIN_CLASS_NAME)

    # RULE 2. digitalizePhysicalEntity
    pimClasses, pimRelations = digitalizePhysicalEntity(cimClasses, cimRelations, pimClasses, pimRelations)

    #RULE 3. transformTemporalEntity
    pimClasses, pimRelations = transformTemporalEntity(cimClasses, cimRelations, pimClasses, pimRelations)

    # RULE 4. transformTemporalEntity
    pimClasses, pimRelations = mergeShadowModelFlow(cimClasses, cimRelations, pimClasses, pimRelations)

    # RULE 5. transformSensor
    pimClasses, pimRelations = transformSensor(cimClasses, cimRelations, pimClasses, pimRelations)

    # RULE 6. transformActuator
    pimClasses, pimRelations = transformActuator(cimClasses, cimRelations, pimClasses, pimRelations)

    # RULE 7. integrateServiceFeedback
    pimClasses, pimRelations = integrateServiceFeedback(cimClasses, cimRelations, pimClasses, pimRelations)

    # RULE 8. integrateDataManager
    pimClasses, pimRelations = integrateDataManager(pimClasses, pimRelations)

    return pimClasses, pimRelations


############################### RULE1: mapToPhysicalTwin  ##############################
def createPhysicalTwinClasses(childClasses, existingIds, idLength):
    """
    Create new 'PhysicalTwin' classes corresponding to the real-world system.

    Args:
        childClasses (pd.DataFrame): DataFrame of classes representing the real-world system.
        existingIds (set): Set of existing class IDs for uniqueness.
        idLength (int): Length of the generated class IDs.

    Returns:
        pd.DataFrame: DataFrame of newly created 'PhysicalTwin' classes.
    """
    pimClasses = []

    for _, row in childClasses.iterrows():
        childClassName = row['To Class Name']

        # Generate a new unique ID and append 'PhysicalTwin' to the class name
        newId = generateId(existingIds, length=idLength)
        newClassName = childClassName + 'PhysicalTwin'

        # Add the new 'PhysicalTwin' class to the list
        pimClasses.append({
            'Class ID': newId,
            'Class Name': newClassName
        })

        # Track the new ID in existingIds to maintain uniqueness
        existingIds.add(newId)

    return pd.DataFrame(pimClasses)
def mapToPhysicalTwin(cimClasses, cimRelations, parentClassName):
    """
    Map a system class from CIM to its respective 'PhysicalTwin' classes in PIM.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        parentClassName (str): The name of the parent class from which the child classes are mapped
                               to their 'PhysicalTwin' counterparts.

    Returns:
        pd.DataFrame: DataFrame of newly created 'PhysicalTwin' classes with unique IDs.
    """
    # Step 1: Get the length of existing class IDs and the list of existing IDs
    idLength = getIdLength(cimClasses)
    existingIds = getExistingIds(cimClasses)
    # Step 2: Find all child classes that have a generalization relationship with the specified parent class
    parentClassId = cimClasses[cimClasses['Class Name'] == parentClassName]['Class ID'].values[0]
    childClasses = findGeneralizationChildClasses(cimRelations, parentClassId)
    # Step 3: Create 'PhysicalTwin' classes for the identified child classes
    dfPimClasses = createPhysicalTwinClasses(childClasses, existingIds, idLength)

    return dfPimClasses


############################### RULE2: digitalizePhysicalEntity ##############################
def searchPhysicalEntityClass(cimClasses, physicalEntityName):
    """
    Search for the class ID of a real-world system in the CIM classes by its name.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        physicalEntityName (str): The name of the physical entity class to search for.

    Returns:
        str: The class ID of the physical enitty class, or None if not found.
    """
    return findClassId(cimClasses, physicalEntityName)
def searchPhysicalEntities(cimClasses, physicalEntityId, cimRelations):
    """
    Search for all child classes of physical entities type.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        physicalEntityId (str): The ID of the phsyical entity class.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.

    Returns:
        pd.DataFrame: DataFrame of child classes of the phsyical entity class.
    """
    return findGeneralizationChildClasses(cimRelations, physicalEntityId)
def createDigitalModels(cimClasses, cimRelations, existingIds, idLength):
    """
    Create corresponding DigitalModel classes for each physical entity to be digitally replicated.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.
        realSystemName (str): The name of the real system to search for.

    Returns:
        list: List of newly created PIM classes (Digital Models).
    """
    # Search for child classes of the real system (e.g., RealCity)
    physicalEntitiesID = searchPhysicalEntityClass(cimClasses, PHYSICAL_ENTITY_CLASS_NAME)

    if not physicalEntitiesID:
        print(f"Warning: No RealSystem class found with name '{PHYSICAL_ENTITY_CLASS_NAME}'.")
        return []

    realSystems = searchPhysicalEntities(cimClasses, physicalEntitiesID, cimRelations)
    digitalModels = []

    for _, row in realSystems.iterrows():
        cimClassName = row['To Class Name']
        # Generate new ID and create the DigitalModel class
        newId = generateId(existingIds, idLength)
        newClassName = 'Digital' + cimClassName
        digitalModels.append({
            'Class ID': newId,
            'Class Name': newClassName
        })
        # Add new ID to the existing set to ensure uniqueness
        existingIds.add(newId)

    return digitalModels
def addDigitalModel(existingIds, idLength):
    """
    Add the DigitalModel class to the PIM model.

    Args:
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalModel class.
    """
    # Generate a unique ID for the DigitalModel class
    digitalModelId = generateId(existingIds, idLength)
    existingIds.add(digitalModelId)
    return digitalModelId
def addDigitalModelManager(existingIds, idLength):
    """
    Add the DigitalModelManager class to the PIM model.

    Args:
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalModelManager class.
    """

    digitalModelManagerId = generateId(existingIds, idLength)
    existingIds.add(digitalModelManagerId)
    return digitalModelManagerId
def createDigitalRelations(cimClasses, cimRelations, newPimClasses, pimRelations):
    """
    Create digital relationships (associations, aggregations, compositions) between digital model classes.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        newPimClasses (pd.DataFrame): DataFrame of newly created digital model classes.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with digital model relationships added.
    """

    newRelationships = []
    processedRelationships = set()  # To track already processed relationships and avoid duplicates

    # Loop through each new digital model class
    for _, newPimClassRow in newPimClasses.iterrows():
        # Extract the original class name by removing 'Model' from the new digital class name
        digitalClassName = newPimClassRow['Class Name']
        originalClassName = digitalClassName.replace('Digital', '')

        # Find the corresponding CIM class with the same original class name
        cimClass = cimClasses[cimClasses['Class Name'] == originalClassName]

        # Skip if no matching CIM class is found
        if cimClass.empty:
            print(f"Warning: No corresponding CIM class found for {digitalClassName}.")
            continue

        cimClassId = cimClass['Class ID'].values[0]

        # Find all relationships in CIM where the current CIM class is involved (as either 'from' or 'to')
        relatedCimRelations = findRelatedRelationships(cimRelations, cimClassId)

        # Loop through each related relationship and find the digital counterparts
        for _, relationRow in relatedCimRelations.iterrows():
            fromId, toId = None, None
            relationType = relationRow['Relationship Type']
            aggregationKind = None  # Default to None unless it's aggregation/composition

            # Determine the correct digital model class names for 'from' and 'to'
            if relationRow['From Class ID'] == cimClassId:
                fromId = newPimClassRow['Class ID']
                toClassName = 'Digital' + relationRow['To Class Name']  # Convert CIM class to digital model name
                toId = findClassId(newPimClasses, toClassName)
            elif relationRow['To Class ID'] == cimClassId:
                toId = newPimClassRow['Class ID']
                fromClassName = 'Digital' + relationRow['From Class Name']
                fromId = findClassId(newPimClasses, fromClassName)

            # Skip if either of the digital classes isn't found
            if not fromId or not toId:
                continue

            # Handling different types of relationships based on CIM relationships
            if relationType == 'Aggregation':
                aggregationKind = 'Shared'  # Default is shared aggregation
                relationType = 'Aggregation'  # Both Aggregation and Composition are treated as Aggregation

            elif relationType == 'Composition':
                aggregationKind = 'Composite'  # Composition has aggregation kind 'composite'
                relationType = 'Aggregation'  # Composition is treated as a type of Aggregation

            elif relationType == 'Association':
                aggregationKind = None  # Association doesn't need aggregation kind

            elif relationType == 'Generalization':
                aggregationKind = None  # Generalization doesn't involve aggregation
                relationType = 'Generalization'

            # Create a tuple to avoid duplicates
            relationTuple = (fromId, toId, relationType, aggregationKind)

            if relationTuple not in processedRelationships:
                # Add the new relationship between the digital classes
                newRelationships.append({
                    'Relationship Type': relationType,
                    'From Class ID': fromId,
                    'From Class Name': newPimClasses[newPimClasses['Class ID'] == fromId]['Class Name'].values[0],
                    'To Class ID': toId,
                    'To Class Name': newPimClasses[newPimClasses['Class ID'] == toId]['Class Name'].values[0],
                    'Aggregation': aggregationKind
                })
                processedRelationships.add(relationTuple)

    # Append the new relationships to the existing PIM relationships
    pimRelations = pd.concat([pimRelations, pd.DataFrame(newRelationships)], ignore_index=True)
    return pimRelations
def addGeneralizationModels(digitalModels, digitalModelID):
    """
    Add generalization relationships between each DigitalShadow and the DigitalShadow class.

    Args:
        digitalShadows (list): List of DigitalShadow classes.
        digitalShadowId (str): The ID of the DigitalShadow class.

    Returns:
        newGeneralizationRelations:
    """

    newGeneralizationRelations = []
    for model in digitalModels:
        newGeneralizationRelations.append({
            'Relationship Type': 'Generalization',
            'From Class ID': digitalModelID,
            'From Class Name': 'DigitalModel',
            'To Class ID': model['Class ID'],
            'To Class Name': model['Class Name'],
            'Aggregation': None
        })
    return newGeneralizationRelations
def addAggregationModelManager(digitalModelID, digitalModelManagerId, pimRelations):
    """
    Add shared aggregation relationships between each DigitalModel and the DigitalModelManager, checking for duplicates.

    Args:
        digitalModelID (str): The ID of the DigitalModel class.
        digitalModelManagerId (str): The ID of the DigitalModelManager class.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships (with duplicates filtered).
    """
    processedRelations = set()  # Set to track added relationships
    relationTuple = (digitalModelManagerId, digitalModelID, 'Aggregation')
    newAggregationRelation = []

    if relationTuple not in processedRelations:
        newAggregationRelation.append({
            'Relationship Type': 'Aggregation',
            'From Class ID': digitalModelManagerId,
            'From Class Name': 'DigitalModelManager',
            'To Class ID': digitalModelID,
            'To Class Name': 'DigitalModel',
            'Aggregation': 'Shared'
        })
        processedRelations.add(relationTuple)

    # Append the new aggregation relation to pimRelations DataFrame
    newAggregationRelationDf = pd.DataFrame(newAggregationRelation)
    pimRelations = pd.concat([pimRelations, newAggregationRelationDf], ignore_index=True)
    return pimRelations
def digitalizePhysicalEntity(cimClasses, cimRelations, pimClasses, pimRelations):
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)
    digitalModels = createDigitalModels(cimClasses, cimRelations, existingIds, idLength)
    newDigitalModels = pd.DataFrame(digitalModels)
    pimClasses = pd.concat([pimClasses, newDigitalModels], ignore_index=True)
    pimRelations = createDigitalRelations(cimClasses, cimRelations, newDigitalModels, pimRelations)

    digitalModelID = addDigitalModel(existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': digitalModelID, 'Class Name': 'DigitalModel'}])],
                           ignore_index=True)
    newGeneralizationRelations = addGeneralizationModels(digitalModels, digitalModelID)
    pimRelations = pd.concat([pimRelations, pd.DataFrame(newGeneralizationRelations)], ignore_index=True)

    digitalModelManagerID = addDigitalModelManager(existingIds, idLength)
    pimClasses = pd.concat(
        [pimClasses, pd.DataFrame([{'Class ID': digitalModelManagerID, 'Class Name': 'DigitalModelManager'}])],
        ignore_index=True)
    pimRelations = addAggregationModelManager(digitalModelID, digitalModelManagerID, pimRelations)

    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'],
                                                keep='first', ignore_index=True)

    return pimClasses, pimRelations


############################### RULE3: transformTemporalEntity ##############################
def searchTemporalEntityClass(cimClasses):
    """
    Search for the TemporalEntity class ID in the CIM classes.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.

    Returns:
        str: The class ID of the TemporalEntity class.
    """
    return findClassId(cimClasses, TEMPORAL_ENTITY_CLASS_NAME)
def searchTemporalEntities(cimClasses, temporalEntityId, cimRelations):
    """
    Search for all child classes of the TemporalEntity class.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        temporalEntityId (str): The ID of the TemporalEntity class.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.

    Returns:
        pd.DataFrame: DataFrame of child classes of the TemporalEntity.
    """
    return findGeneralizationChildClasses(cimRelations, temporalEntityId)
def createDigitalShadows(cimClasses, cimRelations, existingIds, idLength):
    """
    Create corresponding DigitalShadow classes for each TemporalEntity child class.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        list: List of newly created PIM classes (Digital Shadows).
    """
    # Search for child classes of TemporalEntity
    temporalEntityId = searchTemporalEntityClass(cimClasses)
    temporalEntities = searchTemporalEntities(cimClasses, temporalEntityId, cimRelations)
    digitalShadows = []

    for _, row in temporalEntities.iterrows():
        cimClassName = row['To Class Name']
        # Generate new ID and create the shadow class
        newId = generateId(existingIds, idLength)
        newClassName = cimClassName + 'Shadow'
        digitalShadows.append({
            'Class ID': newId,
            'Class Name': newClassName
        })
        # Add new ID to the existing set to ensure uniqueness
        existingIds.add(newId)

    return digitalShadows
def addDigitalShadow(existingIds, idLength):
    """
    Add the DigitalShadow class to the PIM model.

    Args:
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalShadow class.
    """
    digitalShadowId = generateId(existingIds, idLength)
    existingIds.add(digitalShadowId)
    return digitalShadowId
def addDigitalShadowManager(existingIds, idLength):
    """
    Add the DigitalShadowManager class to the PIM model.

    Args:
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalShadowManager class.
    """
    digitalShadowManagerId = generateId(existingIds, idLength)
    existingIds.add(digitalShadowManagerId)
    return digitalShadowManagerId
def addGeneralizationShadows(digitalShadows, digitalShadowId):
    """
    Add generalization relationships between each DigitalShadow and the DigitalShadow class.

    Args:
        digitalShadows (list): List of DigitalShadow classes.
        digitalShadowId (str): The ID of the DigitalShadow class.

    Returns:
        newGeneralizationRelations:
    """

    newGeneralizationRelations = []
    for shadow in digitalShadows:
        newGeneralizationRelations.append({
            'Relationship Type': 'Generalization',
            'From Class ID': digitalShadowId,
            'From Class Name': 'DigitalShadow',
            'To Class ID': shadow['Class ID'],
            'To Class Name': shadow['Class Name'],
            'Aggregation': None
        })
    return newGeneralizationRelations
def addAggregationManager(digitalShadowID, digitalShadowManagerId, pimRelations):
    """
    Add shared aggregation relationships between each DigitalShadow and the DigitalShadowManager, checking for duplicates.

    Args:
        digitalShadowID (str): The ID of the DigitalShadow class.
        digitalShadowManagerId (str): The ID of the DigitalShadowManager class.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships (with duplicates filtered).
    """
    processedRelations = set()  # Set to track added relationships
    relation_tuple = (digitalShadowManagerId, digitalShadowID, 'Aggregation')
    newAggregationRelation = []

    if relation_tuple not in processedRelations:
        newAggregationRelation.append({
            'Relationship Type': 'Aggregation',
            'From Class ID': digitalShadowManagerId,
            'From Class Name': 'DigitalShadowManager',
            'To Class ID': digitalShadowID,
            'To Class Name': 'DigitalShadow',
            'Aggregation': 'Shared'
        })
        processedRelations.add(relation_tuple)

    # Append the new aggregation relation to pimRelations DataFrame
    newAggregationRelationDf = pd.DataFrame(newAggregationRelation)
    pimRelations = pd.concat([pimRelations, newAggregationRelationDf], ignore_index=True)

    return pimRelations
def transformTemporalEntity(cimClasses, cimRelations, pimClasses, pimRelations):
    """
    Transforms Temporal Entities into Digital Shadows and manages relationships.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        pimClasses (pd.DataFrame): DataFrame of PIM classes.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame, pd.DataFrame: Updated PIM classes and relationships DataFrames.
    """
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)

    # Create Digital Shadows and add them to PIM classes
    digitalShadows = createDigitalShadows(cimClasses, cimRelations, existingIds, idLength)
    newDigitalShadowsDf = pd.DataFrame(digitalShadows)
    pimClasses = pd.concat([pimClasses, newDigitalShadowsDf], ignore_index=True)

    # Add DigitalShadow class
    digitalShadowID = addDigitalShadow(existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': digitalShadowID, 'Class Name': 'DigitalShadow'}])], ignore_index=True)

    # Add Generalization relationships between DigitalShadows and DigitalShadow class
    newGeneralizationRelations = addGeneralizationShadows(digitalShadows, digitalShadowID)
    pimRelations = pd.concat([pimRelations, pd.DataFrame(newGeneralizationRelations)],ignore_index=True)

    # Add DigitalShadowManager and its relationships
    digitalShadowManagerID = addDigitalShadowManager(existingIds, idLength)
    pimClasses = pd.concat(
        [pimClasses, pd.DataFrame([{'Class ID': digitalShadowManagerID, 'Class Name': 'DigitalShadowManager'}])], ignore_index=True)

    # Add shared aggregation relationships between DigitalShadows and DigitalShadowManager
    pimRelations = addAggregationManager(digitalShadowID, digitalShadowManagerID, pimRelations)

    # Remove duplicates from PIM relationships and classes
    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'], keep='first', ignore_index=True)

    return pimClasses, pimRelations


############################### RULE4: mergeShadowModelFlow ##############################
def addDigitalTwinManager(existingIds, idLength):
    """
    Add the DigitalTwinManager class to the PIM model.

    Args:
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalTwinManager class.
    """
    digitalTwinManagerId = generateId(existingIds, idLength)
    existingIds.add(digitalTwinManagerId)
    return digitalTwinManagerId
def addDigitalRepresentation(existingIds, idLength):
    """
    Add the DigitalRepresentation class to the PIM model.

    Args:
        existingIds (set): Set of existing class IDs.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalRepresentation class.
    """
    digitalRepresentationId = generateId(existingIds, idLength)
    existingIds.add(digitalRepresentationId)
    return digitalRepresentationId
def addAggregationTwinManager(digitalTwinManagerId, digitalShadowManagerId, digitalModelManagerId, pimRelations):
    """
    Add shared aggregation relationships between the DigitalTwinManager and both the DigitalShadowManager
    and DigitalModelManager classes.

    Args:
        digitalTwinManagerId (str): The ID of the DigitalTwinManager class.
        digitalShadowManagerId (str): The ID of the DigitalShadowManager class.
        digitalModelManagerId (str): The ID of the DigitalModelManager class.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with the aggregation relationships added.
    """
    processedRelations = set(pimRelations[['From Class ID', 'To Class ID', 'Relationship Type']].apply(tuple, axis=1))
    newAggregationRelation = []

    # Aggregation between DigitalTwinManager and DigitalShadowManager
    relation_tuple = (digitalTwinManagerId, digitalShadowManagerId, 'Aggregation')
    if relation_tuple not in processedRelations:
        newAggregationRelation.append({
            'Relationship Type': 'Aggregation',
            'From Class ID': digitalTwinManagerId,
            'From Class Name': 'DigitalTwinManager',
            'To Class ID': digitalShadowManagerId,
            'To Class Name': 'DigitalShadowManager',
            'Aggregation': 'Shared'
        })
        processedRelations.add(relation_tuple)

    # Aggregation between DigitalTwinManager and DigitalModelManager
    relation_tuple = (digitalTwinManagerId, digitalModelManagerId, 'Aggregation')
    if relation_tuple not in processedRelations:
        newAggregationRelation.append({
            'Relationship Type': 'Aggregation',
            'From Class ID': digitalTwinManagerId,
            'From Class Name': 'DigitalTwinManager',
            'To Class ID': digitalModelManagerId,
            'To Class Name': 'DigitalModelManager',
            'Aggregation': 'Shared'
        })
        processedRelations.add(relation_tuple)

    # Append the new aggregation relation to pimRelations DataFrame
    newAggregationRelationDf = pd.DataFrame(newAggregationRelation)
    pimRelations = pd.concat([pimRelations, newAggregationRelationDf], ignore_index=True)

    return pimRelations
def addGeneralizationRepresentation(digitalRepresentationId, digitalShadowID, digitalModelID, pimRelations):
    """
    Add generalization relationships between DigitalRepresentation and both DigitalShadow
    and DigitalModel classes.

    Args:
        digitalRepresentationId (str): The ID of the DigitalRepresentation class.
        digitalShadowID (str): The ID of the DigitalShadow class.
        digitalModelID (str): The ID of the DigitalModel class.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with the generalization relationships added.
    """

    processedRelations = set(pimRelations[['From Class ID', 'To Class ID', 'Relationship Type']].apply(tuple, axis=1))
    newGeneralizationRelations = []

    relation_tuple = (digitalRepresentationId, digitalShadowID, 'Generalization')
    if relation_tuple not in processedRelations:
        newGeneralizationRelations.append({
            'Relationship Type': 'Generalization',
            'From Class ID': digitalRepresentationId,
            'From Class Name': 'DigitalRepresentation',
            'To Class ID': digitalShadowID,
            'To Class Name': 'DigitalDataTrace',
            'Aggregation': None
        })
        processedRelations.add(relation_tuple)

    relation_tuple = (digitalRepresentationId, digitalModelID, 'Generalization')
    if relation_tuple not in processedRelations:
        newGeneralizationRelations.append({
            'Relationship Type': 'Generalization',
            'From Class ID': digitalRepresentationId,
            'From Class Name': 'DigitalRepresentation',
            'To Class ID': digitalModelID,
            'To Class Name': 'DigitalModel',
            'Aggregation': None
        })
        processedRelations.add(relation_tuple)

    newGeneralizationRelationDf = pd.DataFrame(newGeneralizationRelations)
    pimRelations = pd.concat([pimRelations, newGeneralizationRelationDf], ignore_index=True)
    return pimRelations
def mergeShadowModelFlow(cimClasses, cimRelations, pimClasses, pimRelations):
    """
    This function merges the digital representations of the system by combining the Digital Shadow and Digital Model flows.

    The digital data traces are grouped into Digital Shadows and managed by a Digital Shadow Manager,
    while the Digital Models represent the physical entities of the real systems. The flows are merged at the top
    by introducing a Digital Twin Manager class, which serves as a central access point to both the Digital Shadow Manager
    and the Digital Model Manager.

    Additionally, the flows are unified at the bottom by a Digital Representation class,
    which abstracts the physical system (i.e., the physical twin in the Digital Twin architecture).
    The Digital Model and Digital Data Trace classes, representing the structural and behavioral aspects of the system,
    are connected to the Digital Representation class through generalization-specialization relationships,
    where Digital Representation is the parent class.

    Args:
        cimClasses (pd.DataFrame): The CIM classes DataFrame representing the original system.
        cimRelations (pd.DataFrame): The CIM relationships DataFrame for the original system.
        pimClasses (pd.DataFrame): The PIM classes DataFrame to which the new digital classes will be added.
        pimRelations (pd.DataFrame): The PIM relationships DataFrame to which the new relationships will be added.

    Returns:
        pd.DataFrame: Updated PIM classes with the newly added Digital Twin, Shadow, and Model elements.
        pd.DataFrame: Updated PIM relationships with the newly added generalization and aggregation relationships.
    """

    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)

    # Add DigitalTwinManager and DigitalRepresentation
    digitalTwinManagerID = addDigitalTwinManager(existingIds, idLength)
    digitalRepresentationID = addDigitalRepresentation(existingIds, idLength)

    # Add DigitalTwinManager and DigitalRepresentation to pimClasses
    pimClasses = pd.concat(
        [pimClasses, pd.DataFrame([{'Class ID': digitalTwinManagerID, 'Class Name': 'DigitalTwinManager'}])], ignore_index=True)
    pimClasses = pd.concat(
        [pimClasses, pd.DataFrame([{'Class ID': digitalRepresentationID, 'Class Name': 'DigitalRepresentation'}])], ignore_index=True)

    # Get DigitalShadowManager and DigitalModelManager IDs
    digitalShadowManagerID = pimClasses[pimClasses['Class Name'] == 'DigitalShadowManager']['Class ID'].values[0]
    digitalModelManagerID = pimClasses[pimClasses['Class Name'] == 'DigitalModelManager']['Class ID'].values[0]

    # Add shared aggregation relationships between DigitalTwinManager, DigitalShadowManager, and DigitalModelManager
    pimRelations = addAggregationTwinManager(digitalTwinManagerID, digitalShadowManagerID, digitalModelManagerID, pimRelations)

    # Get DigitalDataTrace and DigitalModel IDs
    digitalShadowID = pimClasses[pimClasses['Class Name'] == 'DigitalShadow']['Class ID'].values[0]
    digitalModelID = pimClasses[pimClasses['Class Name'] == 'DigitalModel']['Class ID'].values[0]

    # Add generalization relationships between DigitalRepresentation, DigitalShadow, and DigitalModel
    pimRelations = addGeneralizationRepresentation(digitalRepresentationID, digitalShadowID, digitalModelID, pimRelations)

    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'], keep='first', ignore_index=True)
    return pimClasses, pimRelations

############################### RULE5: transformSensor ##############################
def searchSensorEntityClass(cimClasses: pd.DataFrame) -> str:
    """
    Search for the class ID of a sensor entity in the CIM classes by its name.

    Args:
        cimClasses (pd.DataFrame): DataFrame containing CIM classes.

    Returns:
        str: The class ID of the sensor entity class, or None if not found.
    """
    return findClassId(cimClasses, SENSOR_ENTITY_CLASS_NAME)
def searchSensorEntities(cimClasses: pd.DataFrame, sensorEntityId: str, cimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Search for all child classes of the specified sensor entity type based on generalization relationships.

    Args:
        cimClasses (pd.DataFrame): DataFrame containing CIM classes.
        sensorEntityId (str): The ID of the sensor entity class.
        cimRelations (pd.DataFrame): DataFrame containing CIM relationships.

    Returns:
        pd.DataFrame: DataFrame containing child classes of the sensor entity class.
    """
    return findGeneralizationChildClasses(cimRelations, sensorEntityId)
def addP2DAdapters(dataProviders: list, existingIds: set, idLength: int, pimClasses: pd.DataFrame) -> tuple:
    """
    Add P2DAdapter classes for each sensor/data provider to the PIM model.
    If there's only one data provider, uses a generic name 'P2DAdapter'.
    If there are multiple providers, the adapter name is derived from the provider's name
    with 'DataProvider' removed.

    Args:
        dataProviders (list): List of data provider classes for which P2DAdapters will be created.
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.
        pimClasses (pd.DataFrame): DataFrame of PIM classes to which the new adapters will be added.

    Returns:
        tuple: (list of new P2DAdapter classes, updated DataFrame of PIM classes with P2DAdapters).
    """
    newClasses = []

    # If there's only one provider, use the generic name 'P2DAdapter'
    if len(dataProviders) == 1:
        newAdapterID = generateId(existingIds, idLength)
        existingIds.add(newAdapterID)
        newClasses.append({
            'Class ID': newAdapterID,
            'Class Name': 'P2DAdapter'
        })
    else:
        # If there are multiple providers, create unique adapter names
        for provider in dataProviders:
            newAdapterID = generateId(existingIds, idLength)
            existingIds.add(newAdapterID)
            # Remove 'DataProvider' from the provider name
            className = provider['Class Name'].replace('DataProvider', '')
            newClasses.append({
                'Class ID': newAdapterID,
                'Class Name': 'P2DAdapter' + className
            })

    # Append new adapter classes to PIM classes DataFrame
    pimClasses = pd.concat([pimClasses, pd.DataFrame(newClasses)], ignore_index=True)

    return newClasses, pimClasses
def createDataProviders(cimClasses: pd.DataFrame, cimRelations: pd.DataFrame, existingIds: set, idLength: int) -> list:
    """
    Create digital data provider classes for each sensor entity found in the CIM classes.

    Args:
        cimClasses (pd.DataFrame): DataFrame containing CIM classes.
        cimRelations (pd.DataFrame): DataFrame containing CIM relationships.
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        list: List of dictionaries, each representing a new data provider class for a sensor entity.
    """
    # Search for the sensor entity class in CIM classes
    sensorID = searchSensorEntityClass(cimClasses)
    if not sensorID:
        print(f"Warning: No Sensor entity class found with name '{SENSOR_ENTITY_CLASS_NAME}'.")
        return []

    # Search for all child entities of the sensor class
    sensorEntities = searchSensorEntities(cimClasses, sensorID, cimRelations)
    dataProviders = []

    # Create data providers for each sensor entity
    for _, row in sensorEntities.iterrows():
        cimClassName = row['To Class Name']
        newId = generateId(existingIds, idLength)
        newClassName = cimClassName + 'DataProvider'
        dataProviders.append({
            'Class ID': newId,
            'Class Name': newClassName
        })
        existingIds.add(newId)

    return dataProviders
def addAdapter(existingIds: set, idLength: int) -> str:
    """
    Add a DigitalShadowManager class to the PIM model by generating a unique ID.

    Args:
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DigitalShadowManager class.
    """
    adapterID = generateId(existingIds, idLength)
    existingIds.add(adapterID)
    return adapterID
def addGeneralizationAdapters(adaptersList: list, adapterID: str, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add generalization relationships between each adapter and the DigitalShadow class.

    Args:
        adaptersList (list): List of adapter classes.
        adapterID (str): The ID of the DigitalShadow class (or another central class to which adapters relate).
        pimRelations (pd.DataFrame): DataFrame containing PIM relationships.

    Returns:
        pd.DataFrame: Updated DataFrame with new generalization relationships added.
    """
    newGeneralizationRelations = []
    for adapter in adaptersList:
        newGeneralizationRelations.append({
            'Relationship Type': 'Generalization',
            'From Class ID': adapterID,
            'From Class Name': 'Adapter',
            'To Class ID': adapter['Class ID'],
            'To Class Name': adapter['Class Name'],
            'Aggregation': None
        })

    newGeneralizationRelationDf = pd.DataFrame(newGeneralizationRelations)
    pimRelations = pd.concat([pimRelations, newGeneralizationRelationDf], ignore_index=True)

    return pimRelations
def addUseProviders(providersList: list, adaptersList: list, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Usage' relationships between data providers and adapters in the PIM model.

    Args:
        providersList (list): List of provider classes (DataProviders) represented as dictionaries with 'Class ID' and 'Class Name'.
        adaptersList (list): List of adapter classes (P2DAdapters) represented as dictionaries with 'Class ID' and 'Class Name'.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships DataFrame with new 'Usage' relationships added.
    """
    newUseRelations = []

    # Case for a single provider and a single adapter
    if len(providersList) == 1 and len(adaptersList) == 1:
        newUseRelations.append({
            'Relationship Type': 'Usage',
            'From Class ID': providersList[0]['Class ID'],  # Use the first item from providersList
            'From Class Name': providersList[0]['Class Name'],
            'To Class ID': adaptersList[0]['Class ID'],  # Use the first item from adaptersList
            'To Class Name': adaptersList[0]['Class Name'],
            'Aggregation': None
        })
    else:
        # Case for multiple providers and adapters
        for provider in providersList:
            providerName = provider['Class Name'].replace('DataProvider', '')
            # Find the corresponding adapter class based on the provider's name
            adapter = next(
                (adapter for adapter in adaptersList if adapter['Class Name'] == 'P2DAdapter' + providerName),
                None
            )

            if adapter:
                newUseRelations.append({
                    'Relationship Type': 'Usage',
                    'From Class ID': provider['Class ID'],
                    'From Class Name': provider['Class Name'],
                    'To Class ID': adapter['Class ID'],
                    'To Class Name': adapter['Class Name'],
                    'Aggregation': None
                })

    # Append new 'Usage' relationships to the PIM relationships DataFrame
    newUseRelationsDf = pd.DataFrame(newUseRelations)
    pimRelations = pd.concat([pimRelations, newUseRelationsDf], ignore_index=True)

    return pimRelations

def addPhysicalTwinAggregation(pimClasses, dataProviders, pimRelations):
    """
    Add aggregation relationships between the PhysicalTwin class and DataProvider classes.

    Args:
        pimClasses (pd.DataFrame): DataFrame of PIM classes.
        dataProviders (list): List of DataProvider class dictionaries.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships DataFrame.
    """
    # Find the PhysicalTwin class in PIM classes
    physicalTwin = findClassesByPartialName(pimClasses, PIM_REAL_TWIN_CLASS_NAME)
    if physicalTwin.empty:
        raise ValueError("PhysicalTwin class not found in PIM classes.")

    # Use the first matched PhysicalTwin class
    physicalTwinId = physicalTwin.iloc[0]['Class ID']
    physicalTwinName = physicalTwin.iloc[0]['Class Name']

    # Add an aggregation relationship for each DataProvider
    for provider in dataProviders:
        providerId = provider['Class ID']
        providerName = provider['Class Name']

        newRelation = {
            'Relationship Type': 'Aggregation',
            'From Class ID': physicalTwinId,
            'From Class Name': physicalTwinName,
            'To Class ID': providerId,
            'To Class Name': providerName,
            'Aggregation': 'Shared'
        }
        pimRelations = pd.concat([pimRelations, pd.DataFrame([newRelation])], ignore_index=True)

    return pimRelations
def transformSensor(cimClasses, cimRelations, pimClasses, pimRelations):
    """
    Transform Sensor-related CIM classes and relationships into PIM classes and relationships.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        pimClasses (pd.DataFrame): DataFrame of PIM classes.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        tuple: Updated PIM classes and relationships DataFrames.
    """
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)

    # Step 1: Create DataProvider classes
    dataProviders = createDataProviders(cimClasses, cimRelations, existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame(dataProviders)], ignore_index=True)

    # Step 2: Add PhysicalTwin-to-DataProvider aggregation relationships
    pimRelations = addPhysicalTwinAggregation(pimClasses, dataProviders, pimRelations)

    # Step 3: Add P2D Adapters
    adaptersList, pimClasses = addP2DAdapters(dataProviders, existingIds, idLength, pimClasses)

    # Step 4: Add the "Adapter" class
    adapterID = addAdapter(existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': adapterID, 'Class Name': 'Adapter'}])], ignore_index=True)

    # Step 5: Add Generalization relationships for Adapters
    pimRelations = addGeneralizationAdapters(adaptersList, adapterID, pimRelations)

    # Step 6: Add "Use" relationships for Data Providers
    pimRelations = addUseProviders(dataProviders, adaptersList, pimRelations)

    # Remove duplicates
    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'],
                                                keep='first', ignore_index=True)

    return pimClasses, pimRelations

############################### RULE6: transformActuator ##############################
def searchActuatorEntityClass(cimClasses: pd.DataFrame) -> str:
    """
    Search for the class ID of an actuator entity in the CIM classes by its name.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.

    Returns:
        str: The class ID of the actuator entity class, or None if not found.
    """
    return findClassId(cimClasses, ACTUATOR_ENTITY_CLASS_NAME)
def searchActuatorEntities(cimClasses: pd.DataFrame, actuatorEntityId: str, cimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Search for all child classes of the actuator entity type.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        actuatorEntityId (str): The ID of the actuator entity class.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.

    Returns:
        pd.DataFrame: DataFrame of child classes of the actuator entity class.
    """
    return findGeneralizationChildClasses(cimRelations, actuatorEntityId)
def addD2PAdapters(dataReceivers: list, existingIds: set, idLength: int, pimClasses: pd.DataFrame) -> tuple:
    """
    Add D2PAdapter classes for each actuator/data receiver to the PIM model.
    If there's only one data receiver, use a generic name 'D2PAdapter'.
    If there are multiple receivers, the adapter name will be the receiver's name
    with 'DataReceiver' removed.

    Args:
        dataReceivers (list): List of data receiver classes to which D2PAdapters will be added.
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.
        pimClasses (pd.DataFrame): DataFrame of PIM classes to which the new adapters will be added.

    Returns:
        tuple: (list of new D2PAdapter classes, updated PIM classes DataFrame with D2PAdapters).
    """
    newClasses = []

    # If there's only one receiver, use the generic name 'D2PAdapter'
    if len(dataReceivers) == 1:
        newAdapterId = generateId(existingIds, idLength)
        existingIds.add(newAdapterId)
        newClasses.append({
            'Class ID': newAdapterId,
            'Class Name': 'D2PAdapter'
        })
    else:
        # If there are multiple receivers, create unique adapter names
        for receiver in dataReceivers:
            newAdapterId = generateId(existingIds, idLength)
            existingIds.add(newAdapterId)
            # Remove 'DataReceiver' from the receiver name
            className = receiver['Class Name'].replace('DataReceiver', '')
            newClasses.append({
                'Class ID': newAdapterId,
                'Class Name': 'D2PAdapter' + className
            })

    # Append new adapter classes to PIM classes DataFrame
    pimClasses = pd.concat([pimClasses, pd.DataFrame(newClasses)], ignore_index=True)

    return newClasses, pimClasses
def createDataReceivers(cimClasses: pd.DataFrame, cimRelations: pd.DataFrame, existingIds: set, idLength: int) -> list:
    """
    Create digital data receivers for each actuator entity found in the CIM classes.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        list: List of newly created data receiver classes (for actuators).
    """
    # Search for the actuator entity class in CIM classes
    actuatorId = searchActuatorEntityClass(cimClasses)
    if not actuatorId:
        print(f"Warning: No Actuator entity class found with name '{ACTUATOR_ENTITY_CLASS_NAME}'.")
        return []

    # Search for all child entities of the actuator class
    actuatorEntities = searchActuatorEntities(cimClasses, actuatorId, cimRelations)
    dataReceivers = []

    # Create data receivers for each actuator entity
    for _, row in actuatorEntities.iterrows():
        cimClassName = row['To Class Name']
        newId = generateId(existingIds, idLength)
        newClassName = cimClassName + 'DataReceiver'
        dataReceivers.append({
            'Class ID': newId,
            'Class Name': newClassName
        })
        existingIds.add(newId)

    return dataReceivers
def addUseReceivers(receiversList: list, adaptersList: list, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Usage' relationships between the data receivers and the adapters in the PIM model.

    Args:
        receiversList (list): List of receiver classes (DataReceivers).
        adaptersList (list): List of adapter classes (D2PAdapters).
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with the new 'Usage' relationships added.
    """
    newUseRelations = []

    # Case for a single receiver and a single adapter
    if len(receiversList) == 1 and len(adaptersList) == 1:
        newUseRelations.append({
            'Relationship Type': 'Usage',
            'From Class ID': adaptersList[0]['Class ID'],  # Use the first item from the adapters list
            'From Class Name': adaptersList[0]['Class Name'],
            'To Class ID': receiversList[0]['Class ID'],  # Use the first item from the receivers list
            'To Class Name': receiversList[0]['Class Name'],
            'Aggregation': None
        })
    else:
        # Multiple receivers case
        for receiver in receiversList:
            receiverName = receiver['Class Name'].replace('DataReceiver', '')
            # Find the corresponding adapter class based on receiver name
            adapter = next(
                (adapter for adapter in adaptersList if adapter['Class Name'] == 'D2PAdapter' + receiverName), None)

            if adapter:
                newUseRelations.append({
                    'Relationship Type': 'Usage',
                    'From Class ID': adapter['Class ID'],
                    'From Class Name': adapter['Class Name'],
                    'To Class ID': receiver['Class ID'],
                    'To Class Name': receiver['Class Name'],
                    'Aggregation': None
                })

    # Append new usage relations to PIM relations DataFrame
    newUseRelationsDf = pd.DataFrame(newUseRelations)
    pimRelations = pd.concat([pimRelations, newUseRelationsDf], ignore_index=True)

    return pimRelations

def transformActuator(cimClasses: pd.DataFrame, cimRelations: pd.DataFrame, pimClasses: pd.DataFrame, pimRelations: pd.DataFrame) -> tuple:
    """
    Transform actuators from the CIM model to data receivers in the PIM model with D2PAdapters.

    This transformation includes:
      - Creating D2PAdapter classes
      - Adding the 'Adapter' superclass if it doesn't already exist
      - Adding usage and generalization relationships between data receivers and adapters

    Args:
        cimClasses (pd.DataFrame): DataFrame containing CIM classes.
        cimRelations (pd.DataFrame): DataFrame containing CIM relationships.
        pimClasses (pd.DataFrame): DataFrame of existing PIM classes.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        tuple: Updated (pimClasses, pimRelations) DataFrames with new classes and relationships.
    """
    # Retrieve existing IDs and determine ID length for new classes
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)

    # Step 1: Create data receivers for actuator entities
    dataReceivers = createDataReceivers(cimClasses, cimRelations, existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame(dataReceivers)], ignore_index=True)

    # Step 2: Add PhysicalTwin-to-DataReceivers aggregation relationships
    pimRelations = addPhysicalTwinAggregation(pimClasses, dataReceivers, pimRelations)

    # Step 3: Add D2PAdapter classes for each data receiver
    adaptersList, pimClasses = addD2PAdapters(dataReceivers, existingIds, idLength, pimClasses)

    # Step 4: Check if 'Adapter' superclass already exists; if not, create it
    if not pimClasses[pimClasses['Class Name'] == 'Adapter'].empty:
        adapterId = pimClasses[pimClasses['Class Name'] == 'Adapter']['Class ID'].values[0]
    else:
        # Create 'Adapter' superclass if it doesn't exist
        adapterId = addAdapter(existingIds, idLength)
        pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': adapterId, 'Class Name': 'Adapter'}])],ignore_index=True)

    # Step 5: Add generalization relationships between adapters and 'Adapter'
    pimRelations = addGeneralizationAdapters(adaptersList, adapterId, pimRelations)

    # Step 6: Add usage relationships between data receivers and adapters
    pimRelations = addUseReceivers(dataReceivers, adaptersList, pimRelations)

    # Step 7: Remove duplicates from PIM classes and relationships
    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'], keep='first', ignore_index=True)

    return pimClasses, pimRelations


############################### RULE7: integrateServiceFeedback ##############################
def addServiceManager(existingIds: set, idLength: int) -> str:
    """
    Add a ServiceManager class to the PIM model.

    The ServiceManager class is responsible for managing service-related feedback and interactions
    within the Digital Twin architecture.

    Args:
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created ServiceManager class.
    """
    serviceId = generateId(existingIds, idLength)
    existingIds.add(serviceId)
    return serviceId
def addFeedback(existingIds: set, idLength: int) -> str:
    """
    Add a Feedback class to the PIM model.

    Feedback represents a mechanism that collects feedback from data receivers to monitor and adjust
    the behavior of the physical system in the Digital Twin architecture.

    Args:
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created Feedback class.
    """
    feedbackId = generateId(existingIds, idLength)
    existingIds.add(feedbackId)
    return feedbackId
def createFeedbackProviders(pimClasses: pd.DataFrame, existingIds: set, idLength: int) -> tuple:
    """
    Create Feedback classes for each DataReceiver class in the PIM model.

    Feedback providers are added for all classes identified as data receivers in the system,
    acting as feedback channels for system data.

    Args:
        pimClasses (pd.DataFrame): DataFrame of PIM classes.
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        tuple: A list of new Feedback providers and the updated PIM classes DataFrame.
    """
    dataReceivers = pimClasses[pimClasses['Class Name'].str.contains('DataReceiver')]
    newFeedbackProviders = []

    for _, receiver in dataReceivers.iterrows():
        feedbackId = addFeedback(existingIds, idLength)
        newFeedbackProviders.append({
            'Class ID': feedbackId,
            'Class Name': 'Feedback' + receiver['Class Name'].replace('DataReceiver', '')
        })

    pimClasses = pd.concat([pimClasses, pd.DataFrame(newFeedbackProviders)], ignore_index=True)
    return newFeedbackProviders, pimClasses
def addAggregationFeedback(feedbackList: list, serviceId: str, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add aggregation relationships between Feedback classes and the ServiceManager class.

    Establishes a composite aggregation relationship between the ServiceManager class and each
    Feedback provider class.

    Args:
        feedbackList (list): List of Feedback classes.
        serviceId (str): The class ID of the ServiceManager.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with the new aggregation relations added.
    """
    newRelations = []
    processedRelations = set()

    for feedback in feedbackList:
        relationTuple = (feedback['Class ID'], serviceId, 'Aggregation')
        if relationTuple not in processedRelations:
            newRelations.append({
                'Relationship Type': 'Aggregation',
                'From Class ID': serviceId,
                'From Class Name': 'ServiceManager',
                'To Class ID': feedback['Class ID'],
                'To Class Name': feedback['Class Name'],
                'Aggregation': 'Composite'
            })
            processedRelations.add(relationTuple)

    newRelationsDf = pd.DataFrame(newRelations)
    pimRelations = pd.concat([pimRelations, newRelationsDf], ignore_index=True)
    return pimRelations
def addUseService(serviceId: str, digitalTwinManagerId: str, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'Usage' relationship between the ServiceManager and DigitalTwinManager classes.

    Creates a usage relationship where the ServiceManager class uses the DigitalTwinManager
    within the Digital Twin architecture.

    Args:
        serviceId (str): The class ID of the ServiceManager.
        digitalTwinManagerId (str): The class ID of the DigitalTwinManager.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with the new 'Usage' relationship added.
    """
    newUseRelations = [{
        'Relationship Type': 'Usage',
        'From Class ID': serviceId,
        'From Class Name': 'ServiceManager',
        'To Class ID': digitalTwinManagerId,
        'To Class Name': 'DigitalTwinManager',
        'Aggregation': None
    }]

    newUseRelationsDf = pd.DataFrame(newUseRelations)
    pimRelations = pd.concat([pimRelations, newUseRelationsDf], ignore_index=True)
    return pimRelations
def addUseFeedbackProviders(feedbackList: list, pimClasses: pd.DataFrame, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Usage' relationships between Feedback classes and their corresponding DataReceiver classes.

    Links each Feedback provider to its corresponding DataReceiver by adding usage relationships
    in the PIM model.

    Args:
        feedbackList (list): List of Feedback classes.
        pimClasses (pd.DataFrame): DataFrame of PIM classes.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships with the new 'Usage' relationships added.
    """
    newRelations = []
    processedRelations = set()

    for feedback in feedbackList:
        feedbackName = feedback['Class Name'].replace('Feedback', '')
        dataReceiver = pimClasses[pimClasses['Class Name'] == (feedbackName + 'DataReceiver')]

        if not dataReceiver.empty:
            dataReceiverId = dataReceiver['Class ID'].values[0]
            dataReceiverName = dataReceiver['Class Name'].values[0]

            relationTuple = (feedback['Class ID'], dataReceiverId, 'Usage')
            if relationTuple not in processedRelations:
                newRelations.append({
                    'Relationship Type': 'Usage',
                    'From Class ID': feedback['Class ID'],
                    'From Class Name': feedback['Class Name'],
                    'To Class ID': dataReceiverId,
                    'To Class Name': dataReceiverName,
                    'Aggregation': None
                })
                processedRelations.add(relationTuple)

    newRelationsDf = pd.DataFrame(newRelations)
    pimRelations = pd.concat([pimRelations, newRelationsDf], ignore_index=True)
    return pimRelations
def integrateServiceFeedback(cimClasses: pd.DataFrame, cimRelations: pd.DataFrame, pimClasses: pd.DataFrame, pimRelations: pd.DataFrame) -> tuple:
    """
    Integrates the ServiceManager and feedback flow into the PIM model, establishing relationships
    with the DigitalTwinManager and feedback providers.

    This function performs the following operations:
      1. Creates a ServiceManager class responsible for managing services within the Digital Twin architecture.
      2. Adds a usage relationship between the ServiceManager and the DigitalTwinManager,
         allowing the ServiceManager to utilize digital twin models.
      3. For each data receiver in the system, creates a corresponding Feedback Provider class.
         These feedback providers serve as channels to monitor and adjust the physical system.
      4. Establishes a composite aggregation relationship between the ServiceManager and
         the Feedback Providers.
      5. Links each Feedback Provider to its corresponding data receiver via a usage relationship.

    Args:
        cimClasses (pd.DataFrame): DataFrame of CIM classes.
        cimRelations (pd.DataFrame): DataFrame of CIM relationships.
        pimClasses (pd.DataFrame): DataFrame of PIM classes.
        pimRelations (pd.DataFrame): DataFrame of PIM relationships.

    Returns:
        tuple: Updated (pimClasses, pimRelations) DataFrames with ServiceManager and feedback flow integrated.
    """
    # Step 1: Retrieve existing class IDs and determine the ID length for unique identification
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)
    # Step 2: Add the ServiceManager class to the PIM model
    serviceId = addServiceManager(existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': serviceId, 'Class Name': 'ServiceManager'}])], ignore_index=True)
    # Step 3: Create Feedback Providers for each data receiver and add them to the PIM model
    feedbackList, pimClasses = createFeedbackProviders(pimClasses, existingIds, idLength)
    # Step 4: Establish aggregation relationships between the ServiceManager and Feedback Providers
    pimRelations = addAggregationFeedback(feedbackList, serviceId, pimRelations)
    # Step 5: Retrieve the DigitalTwinManager ID
    digitalTwinManagerId = pimClasses[pimClasses['Class Name'] == 'DigitalTwinManager']['Class ID'].values[0]
    # Step 6: Establish a usage relationship between the ServiceManager and the DigitalTwinManager
    pimRelations = addUseService(serviceId, digitalTwinManagerId, pimRelations)
    # Step 7: Establish usage relationships between Feedback Providers and their corresponding Data Receivers
    pimRelations = addUseFeedbackProviders(feedbackList, pimClasses, pimRelations)
    # Step 8: Remove duplicates from PIM classes and relationships to ensure data integrity
    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'], keep='first', ignore_index=True)

    return pimClasses, pimRelations


############################### RULE8: integrateDataManager ##############################
def addDataManager(existingIds: set, idLength: int) -> str:
    """
    Add a DataManager class to the PIM model.

    The DataManager class is responsible for managing data flow, ensuring proper communication
    between data models and other components of the Digital Twin system.

    Args:
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DataManager class.
    """
    dataManagerId = generateId(existingIds, idLength)
    existingIds.add(dataManagerId)
    return dataManagerId
def addDataModel(existingIds: set, idLength: int) -> str:
    """
    Add a DataModel class to the PIM model.

    The DataModel class represents the digital models in the Digital Twin architecture that capture
    data about the physical system's behavior and structure.

    Args:
        existingIds (set): Set of existing class IDs to ensure uniqueness.
        idLength (int): Length of generated class IDs.

    Returns:
        str: The class ID of the newly created DataModel class.
    """
    dataModelId = generateId(existingIds, idLength)
    existingIds.add(dataModelId)
    return dataModelId
def addUseDataModel(dataModelId: str, dataManagerId: str,pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 'Usage' relationships between the DataManager and DataModel

    Args:
        dataModelId (str): The ID of the DataModel class.
        dataManagerId (str): The ID of the DataManager class.

    Returns:
        pd.DataFrame: Updated PIM relationships with new 'Usage' relationships added.
    """
    newRelations = [
        {
            'Relationship Type': 'Usage',
            'From Class ID': dataManagerId,
            'From Class Name': 'DataManager',
            'To Class ID': dataModelId,
            'To Class Name': 'DataModel',
            'Aggregation': None
        }
    ]
    newRelationsDf = pd.DataFrame(newRelations)
    pimRelations = pd.concat([pimRelations, newRelationsDf], ignore_index=True)

    return pimRelations
def addUseDataManager(dataManagerId: str, digitalTwinManagerId: str, serviceManagerId: str,adapterId: str, pimRelations: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Usage' relationships between the DataManager and other components in the PIM model.

    This function creates 'Usage' relationships that connect the DataManager to:
      - The ServiceManager (which uses the DataManager to manage services)
      - The DigitalTwinManager (which uses the DataManager to interface with digital models)
      - The Adapter (which uses the DataManager to communicate with physical systems)

    Args:
        dataManagerId (str): The ID of the DataManager class.
        digitalTwinManagerId (str): The ID of the DigitalTwinManager class.
        serviceManagerId (str): The ID of the ServiceManager class.
        adapterId (str): The ID of the Adapter class.
        pimRelations (pd.DataFrame): DataFrame of existing PIM relationships.

    Returns:
        pd.DataFrame: Updated PIM relationships DataFrame with the newly added 'Usage' relationships.
    """

    newUseRelations = [
        {
            'Relationship Type': 'Usage',
            'From Class ID': serviceManagerId,
            'From Class Name': 'ServiceManager',
            'To Class ID': dataManagerId,
            'To Class Name': 'DataManager',
            'Aggregation': None
        },
        {
            'Relationship Type': 'Usage',
            'From Class ID': digitalTwinManagerId,
            'From Class Name': 'DigitalTwinManager',
            'To Class ID': dataManagerId,
            'To Class Name': 'DataManager',
            'Aggregation': None
        },
        {
            'Relationship Type': 'Usage',
            'From Class ID': adapterId,
            'From Class Name': 'Adapter',
            'To Class ID': dataManagerId,
            'To Class Name': 'DataManager',
            'Aggregation': None
        }
    ]

    newUseRelationsDf = pd.DataFrame(newUseRelations)
    pimRelations = pd.concat([pimRelations, newUseRelationsDf], ignore_index=True)

    return pimRelations

def integrateDataManager(pimClasses: pd.DataFrame, pimRelations: pd.DataFrame
) -> tuple:
    """
    Integrate the DataManager and DataModel into the PIM model.

    This function introduces both the DataManager and DataModel classes into the PIM. It establishes relationships between these two classes and relevant adapters, ensuring usage relationships.

    Args:
        pimClasses (pd.DataFrame): DataFrame containing the current PIM classes.
        pimRelations (pd.DataFrame): DataFrame containing the current PIM relationships.

    Returns:
        tuple: Updated (pimClasses, pimRelations) DataFrames with added DataManager, DataModel, and related relationships.
    """

    # Step 1: Get existing IDs and length of IDs
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)

    # Step 2: Add DataManager and DataModel classes
    dataManagerId = addDataManager(existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': dataManagerId, 'Class Name': 'DataManager'}])], ignore_index=True)

    dataModelId = addDataModel(existingIds, idLength)
    pimClasses = pd.concat([pimClasses, pd.DataFrame([{'Class ID': dataModelId, 'Class Name': 'DataModel'}])], ignore_index=True)

    # Step 3: Add 'CompliantWith' relationships between DataManager, DataModel, and adapters
    pimRelations = addUseDataModel(dataModelId, dataManagerId, pimRelations)

    # Retrieve IDs for related components
    digitalTwinManagerId = pimClasses[pimClasses['Class Name'] == 'DigitalTwinManager']['Class ID'].values[0]
    serviceManagerId = pimClasses[pimClasses['Class Name'] == 'ServiceManager']['Class ID'].values[0]
    adapterId = pimClasses[pimClasses['Class Name'] == 'Adapter']['Class ID'].values[0]
    # Step 5: Add 'Usage' relationships between DataManager and key classes
    pimRelations = addUseDataManager(dataManagerId, digitalTwinManagerId, serviceManagerId, adapterId, pimRelations)
    # Step 6: Remove duplicates from the PIM classes and relationships
    pimClasses = pimClasses.drop_duplicates(subset='Class Name', keep='first', ignore_index=True)
    pimRelations = pimRelations.drop_duplicates(subset=['From Class Name', 'To Class Name', 'Relationship Type'],keep='first', ignore_index=True)

    return pimClasses, pimRelations

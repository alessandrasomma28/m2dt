import pandas as pd
from TransformationRules.transformationutils import (findGeneralizationChildClasses, generateId,
                                                     findClassesByPartialName, getIdLength, getExistingIds)
from TransformationRules.constants import (PIM_DIGITAL_MODEL_RELATED_CLASS_NAME, PIM_DIGITAL_RELATED_CLASS_NAME,
                                           PIM_MODEL_MANAGER_CLASS_NAME, PIM_TWIN_MANAGER_CLASS_NAME)


def pim2psmTransformation(pimClasses, pimRelations):
    psmRelations = pd.DataFrame(
        columns=["Relationship Type", "From Class ID", "From Class Name", "To Class ID", "To Class Name",
                 "Aggregation"])

    # RULE 1. transformDigitalModel
    psmClasses, psmRelations = transformDigitalModel(pimClasses, pimRelations, psmRelations)

    # RULE 2. createFiwareContext
    psmClasses, psmRelations = createFiwareContext(psmClasses, psmRelations)

    # RULE 3. transformAdapter

    # RULE 4. transformService

    # RULE 5. integrateData

    return psmClasses, psmRelations


############################### RULE1: transformDigitalModel  ##############################
def transformDigitalModel(pimClasses, pimRelations, psmRelations):
    """
    Transform digital-related PIM classes into a SumoSimulator PSM class.

    Args:
        pimClasses (pd.DataFrame): DataFrame of PIM classes with columns ['Class ID', 'Class Name'].
        pimRelations (pd.DataFrame): DataFrame of PIM relationships with columns ['Relationship Type', 'From Class ID',
                                                                                  'From Class Name', 'To Class ID',
                                                                                  'To Class Name'].
        psmRelations (pd.DataFrame): starting dataframe of PSM relations.

    Returns:
        tuple: A tuple of two DataFrames:
            - pd.DataFrame: DataFrame of PSM classes.
            - pd.DataFrame: DataFrame of PSM relations.
    """
    # Step 1: Find the DigitalRepresentation class
    digitalRepresentation = findClassesByPartialName(pimClasses, PIM_DIGITAL_RELATED_CLASS_NAME)

    # Step 2: Find the DigitalModel classes
    digitalModel = findClassesByPartialName(pimClasses, PIM_DIGITAL_MODEL_RELATED_CLASS_NAME)

    # Step 2.1: Find all children of the DigitalModel classes iteratively
    allChildren = set()
    stack = digitalModel['Class ID'].tolist()  # Initialize stack with IDs of DigitalModel classes

    while stack:
        currentClassId = stack.pop()
        children = findGeneralizationChildClasses(pimRelations, currentClassId)
        for _, childRow in children.iterrows():
            childClassId = childRow['To Class ID']
            if childClassId not in allChildren:  # Avoid duplicates
                allChildren.add(childClassId)
                stack.append(childClassId)  # Add this child to the stack to find its children

    # Map child IDs back to their class names
    childClassNames = pimClasses[pimClasses['Class ID'].isin(allChildren)]['Class Name'].tolist()

    # Step 3: Find the DigitalModelManager class related to DigitalModel
    digitalModelManager = findClassesByPartialName(pimClasses, PIM_MODEL_MANAGER_CLASS_NAME)
    relatedModelManagers = []

    for _, modelRow in digitalModel.iterrows():
        for _, managerRow in digitalModelManager.iterrows():
            # Check if there is a relationship between the manager and the model
            relationExists = not pimRelations[
                (pimRelations['From Class ID'] == managerRow['Class ID']) &
                (pimRelations['To Class ID'] == modelRow['Class ID'])
            ].empty
            if relationExists:
                relatedModelManagers.append(managerRow['Class Name'])

    # Step 4: Create the SumoSimulator PSM class
    existingIds = getExistingIds(pimClasses)
    idLength = getIdLength(pimClasses)
    sumoSimulatorId = generateId(existingIds, idLength)

    # Define the SumoSimulator as a new PSM class
    sumoSimulatorClass = {
        'Class ID': sumoSimulatorId,
        'Class Name': 'SumoSimulator'
    }
    psmClasses = pd.DataFrame([sumoSimulatorClass])

    # Step 5: Find the DigitalTwinManager class and add it to PSM classes
    digitalTwinManager = findClassesByPartialName(pimClasses, PIM_TWIN_MANAGER_CLASS_NAME)
    if not digitalTwinManager.empty:
        # Only add the DigitalTwinManager's ID and Name
        digitalTwinManagerSubset = digitalTwinManager[['Class ID', 'Class Name']]
        psmClasses = pd.concat([psmClasses, digitalTwinManagerSubset], ignore_index=True)

        # Add aggregation relationship between SumoSimulator and DigitalTwinManager
        aggregationRelation = {
            "Relationship Type": "Aggregation",
            "From Class ID": sumoSimulatorId,
            "From Class Name": "SumoSimulator",
            "To Class ID": digitalTwinManagerSubset.iloc[0]['Class ID'],
            "To Class Name": digitalTwinManagerSubset.iloc[0]['Class Name'],
            "Aggregation": "Shared"
        }
        psmRelations = pd.concat([psmRelations, pd.DataFrame([aggregationRelation])], ignore_index=True)

    return psmClasses, psmRelations



############################### RULE2: createFiwareContext  ##############################
def createFiwareContext(psmClasses, psmRelations):
    """
    Create the Fiware Context including ContextBroker, SubscriptionManager, MongoManager, and TimescaleManager.

    Args:
        psmClasses (pd.DataFrame): DataFrame of PSM classes with columns ['Class ID', 'Class Name'].
        psmRelations (pd.DataFrame): DataFrame of PIM relationships with columns ['Relationship Type', 'From Class ID',
                                                                                  'From Class Name', 'To Class ID',
                                                                                  'To Class Name'].

    Returns:
        tuple: A tuple of two DataFrames:
            - pd.DataFrame: Updated DataFrame of PSM classes with added Fiware Context classes.
            - pd.DataFrame: DataFrame of PSM relations defining the relationships among the classes.
    """


    # Generate unique IDs for new classes
    existingIds = getExistingIds(psmClasses)
    idLength = getIdLength(psmClasses)
    contextBrokerId = generateId(existingIds, idLength)
    subscriptionManagerId = generateId(existingIds, idLength)
    mongoManagerId = generateId(existingIds, idLength)
    timescaleManagerId = generateId(existingIds, idLength)

    # Define the ContextBroker class
    contextBrokerClass = {
        'Class ID': contextBrokerId,
        'Class Name': 'ContextBroker'
    }

    # Define the SubscriptionManager, MongoManager, and TimescaleManager classes
    subscriptionManagerClass = {
        'Class ID': subscriptionManagerId,
        'Class Name': 'SubscriptionManager'
    }
    mongoManagerClass = {
        'Class ID': mongoManagerId,
        'Class Name': 'MongoManager'
    }
    timescaleManagerClass = {
        'Class ID': timescaleManagerId,
        'Class Name': 'TimescaleManager'
    }

    # Append new classes to psmClasses DataFrame
    newClasses = pd.DataFrame([contextBrokerClass, subscriptionManagerClass, mongoManagerClass, timescaleManagerClass])
    psmClasses = pd.concat([psmClasses, newClasses], ignore_index=True)

    # Define relationships
    # Association relation between ContextBroker and SubscriptionManager
    psmRelations = pd.concat([
        psmRelations,
        pd.DataFrame([{
            "Relationship Type": "Association",
            "From Class ID": contextBrokerId,
            "From Class Name": "ContextBroker",
            "To Class ID": subscriptionManagerId,
            "To Class Name": "SubscriptionManager",
            "Aggregation": False
        }])
    ], ignore_index=True)

    # Usage relation between ContextBroker and MongoManager
    psmRelations = pd.concat([
        psmRelations,
        pd.DataFrame([{
            "Relationship Type": "Usage",
            "From Class ID": contextBrokerId,
            "From Class Name": "ContextBroker",
            "To Class ID": mongoManagerId,
            "To Class Name": "MongoManager",
            "Aggregation": False
        }])
    ], ignore_index=True)

    return psmClasses, psmRelations


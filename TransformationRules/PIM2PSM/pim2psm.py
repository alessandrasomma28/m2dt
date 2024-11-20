import pandas as pd
from TransformationRules.transformationutils import (findGeneralizationChildClasses, generateId,
                                                     findClassesByPartialName, getIdLength, getExistingIds)
from TransformationRules.constants import PIM_DIGITAL_MODEL_RELATED_CLASS_NAME, PIM_DIGITAL_RELATED_CLASS_NAME, PIM_MODEL_MANAGER_CLASS_NAME

def pim2psmTransformation(pimClasses, pimRelations):
    psmRelations = pd.DataFrame(
        columns=["Relationship Type", "From Class ID", "From Class Name", "To Class ID", "To Class Name",
                 "Aggregation"])

    # RULE 1. transformDigitalModel
    psmClasses = transformDigitalModel(pimClasses, pimRelations)

    # RULE 2. createFiwareContext

    # RULE 3. transformAdapter

    # RULE 4. transformService

    # RULE 5. integrateData

    return psmClasses, psmRelations


def transformDigitalModel(pimClasses, pimRelations):
    """
    Transform digital-related PIM classes into a SumoSimulator PSM class.

    Args:
        pimClasses (pd.DataFrame): DataFrame of PIM classes with columns ['Class ID', 'Class Name'].
        pimRelations (pd.DataFrame): DataFrame of PIM relationships with columns ['Relationship Type', 'From Class ID',
                                                                                  'From Class Name', 'To Class ID',
                                                                                  'To Class Name'].

    Returns:
        pd.DataFrame: DataFrame of PSM classes with columns ['Class ID', 'Class Name'].
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

    # Debugging print statements (you can remove these in production)
    print("Related Model Managers:", relatedModelManagers)
    print("Digital Models:", digitalModel)
    print("Digital Representations:", digitalRepresentation)

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

    return psmClasses

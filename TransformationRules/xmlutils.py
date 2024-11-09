import xml.etree.ElementTree as ET
import pandas as pd
import os

class UMLClass:
    """Class to store UML Class details."""
    def __init__(self, class_id, name):
        self.class_id = class_id
        self.name = name
        self.generalizations = []
        self.specializations = []

##### VP_GENERATED_XML PARSING #######
def parseClasses(rootElement):
    """
    Parse the VP_GENERATED_XML to extract classes and return a dictionary of class IDs and names.

    Args:
        rootElement: VP_GENERATED_XML root element.

    Returns:
        classes: A dictionary of UMLClass objects.
        dfClasses: DataFrame of class IDs and names.
    """
    classes = {}

    for classElement in rootElement.findall(".//Class"):
        classId = classElement.get("Id")
        className = classElement.get("Name")

        if classId and classId not in classes and className not in [cls.name for cls in classes.values()]:
            newClass = UMLClass(class_id=classId, name=className)
            classes[classId] = newClass

    classData = {
        'Class ID': [cls.class_id for cls in classes.values()],
        'Class Name': [cls.name for cls in classes.values()]
    }

    dfClasses = pd.DataFrame(classData)
    return classes, dfClasses
def findAssociations(rootElement, classDict):
    """
    Extract association, aggregation, and composition relationships from the VP_GENERATED_XML.

    Args:
        rootElement: VP_GENERATED_XML root element.
        classDict: Dictionary of UMLClass objects.

    Returns:
        relationships: A list of relationship dictionaries.
    """
    relationships = []

    for associationElement in rootElement.findall(".//Association"):
        fromEndElement = associationElement.find(".//FromEnd/AssociationEnd")
        toEndElement = associationElement.find(".//ToEnd/AssociationEnd")

        if fromEndElement is not None and toEndElement is not None:
            fromClassId = fromEndElement.get("EndModelElement")
            toClassId = toEndElement.get("EndModelElement")

            if fromClassId and toClassId:
                fromClassName = classDict.get(fromClassId, UMLClass(fromClassId, "Unknown")).name
                toClassName = classDict.get(toClassId, UMLClass(toClassId, "Unknown")).name

                aggregation = fromEndElement.get("AggregationKind", "None")
                if aggregation == "Shared":
                    relationshipType = "Aggregation"
                elif aggregation == "Composite":
                    relationshipType = "Composition"
                else:
                    relationshipType = "Association"

                relationships.append({
                    'Relationship Type': relationshipType,
                    'From Class ID': fromClassId,
                    'From Class Name': fromClassName,
                    'To Class ID': toClassId,
                    'To Class Name': toClassName
                })

    return relationships
def findGeneralizations(rootElement, classDict, relationshipList):
    """
    Extract generalization relationships from the VP_GENERATED_XML.

    Args:
        rootElement: VP_GENERATED_XML root element.
        classDict: Dictionary of UMLClass objects.
        relationshipList: List of existing relationships (to append to).

    Returns:
        relationshipList: Updated list of relationships including generalizations.
    """
    for generalizationElement in rootElement.findall(".//Generalization"):
        fromClassId = generalizationElement.get("From")
        toClassId = generalizationElement.get("To")

        if fromClassId and toClassId:
            fromClassName = classDict.get(fromClassId, UMLClass(fromClassId, "Unknown")).name
            toClassName = classDict.get(toClassId, UMLClass(toClassId, "Unknown")).name

            relationshipList.append({
                'Relationship Type': 'Generalization',
                'From Class ID': fromClassId,
                'From Class Name': fromClassName,
                'To Class ID': toClassId,
                'To Class Name': toClassName
            })

    return relationshipList
def filterUnknownClasses(dataFrame):
    """
    Filter out rows from a DataFrame that have 'Unknown' in the class names.

    Args:
        dataFrame: DataFrame containing relationships.

    Returns:
        dataFrame: Filtered DataFrame.
    """
    dataFrame = dataFrame[dataFrame['From Class Name'] != 'Unknown']
    dataFrame = dataFrame[dataFrame['To Class Name'] != 'Unknown']
    return dataFrame
def XMLUMLParser(xmlFilePath):
    """
    Parse an VP_GENERATED_XML file to extract UML classes and relationships,
    returning the class and relationship data as DataFrames.

    Args:
        xmlFilePath: Path to the VP_GENERATED_XML file.

    Returns:
        dfClasses: DataFrame containing UML classes.
        dfRelationships: DataFrame containing UML relationships.
    """
    tree = ET.parse(xmlFilePath)
    rootElement = tree.getroot()
    # Step 1: Parse UML classes
    umlClasses, dfClasses = parseClasses(rootElement)
    # Step 2: Find UML relationships (associations, aggregations, compositions)
    umlRelationships = findAssociations(rootElement, umlClasses)
    # Step 3: Find generalization relationships
    umlRelationships = findGeneralizations(rootElement, umlClasses, umlRelationships)
    # Step 4: Convert relationships to DataFrame
    dfRelationships = pd.DataFrame(umlRelationships)
    # Step 5: Filter out unknown classes
    dfRelationships = filterUnknownClasses(dfRelationships)
    return dfClasses, dfRelationships

### SAVE CLASSES AND RELATIONS TO CSV ###
def saveToCsv(dfClasses, dfRelationships, classesFilePath, relationshipsFilePath):
    """
    Save the classes and relationships DataFrames to specified CSV files.
    Checks if the directories exist; if not, it creates them.
    If files with the same name already exist, they are overwritten.

    Args:
        dfClasses: DataFrame containing classes.
        dfRelationships: DataFrame containing relationships.
        classesFilePath: File path for saving the classes CSV file.
        relationshipsFilePath: File path for saving the relationships CSV file.
    """
    # Ensure the directory for classesFilePath exists
    classesDir = os.path.dirname(classesFilePath)
    if classesDir and not os.path.exists(classesDir):
        os.makedirs(classesDir)
        print(f"Created directory: {classesDir}")

    # Ensure the directory for relationshipsFilePath exists
    relationshipsDir = os.path.dirname(relationshipsFilePath)
    if relationshipsDir and not os.path.exists(relationshipsDir):
        os.makedirs(relationshipsDir)
        print(f"Created directory: {relationshipsDir}")

    # Save DataFrames to CSV, overwriting any existing files
    dfClasses.to_csv(classesFilePath, index=False)
    dfRelationships.to_csv(relationshipsFilePath, index=False)
    print(f"Classes saved to {classesFilePath}")
    print(f"Relationships saved to {relationshipsFilePath}")



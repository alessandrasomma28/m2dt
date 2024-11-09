import xml.etree.ElementTree as ET
import pandas as pd
import random
import string
from xml.dom import minidom
from datetime import datetime
import numpy as np
import time
import inspect
import ast
import types
import uuid


class UMLClass:
    """Class to store UML Class details."""
    def __init__(self, class_id, name):
        self.class_id = class_id
        self.name = name
        self.generalizations = []
        self.specializations = []

##### XML PARSING #######
def parseClasses(rootElement):
    """
    Parse the XML to extract classes and return a dictionary of class IDs and names.

    Args:
        rootElement: XML root element.

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
    Extract association, aggregation, and composition relationships from the XML.

    Args:
        rootElement: XML root element.
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
    Extract generalization relationships from the XML.

    Args:
        rootElement: XML root element.
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
    Parse an XML file to extract UML classes and relationships,
    returning the class and relationship data as DataFrames.

    Args:
        xmlFilePath: Path to the XML file.

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

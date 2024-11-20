import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import os
from TransformationRules.transformationutils import generateId, getExistingIds, getIdLength
from datetime import datetime

def generateTimestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

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


### XML GENERATION ##
def generateXml(inputClasses: pd.DataFrame, inputRelations: pd.DataFrame, projectName: str, fileName: str):
    """
    Generate an XML file representing the provided classes and relationships in the PIM model.

    This function creates a structured XML document with class and relationship elements based on
    the provided DataFrames of classes and relationships.

    Args:
        inputClasses (pd.DataFrame): DataFrame containing PIM classes with 'Class ID' and 'Class Name' columns.
        inputRelations (pd.DataFrame): DataFrame containing PIM relationships with 'Relationship Type', 'From Class ID', 'To Class ID', and optional 'Aggregation' columns.
        projectName (str): The name of the project in which the XML document is included.
        fileName (str): The name of the file where the XML document will be saved.
    """
    # Create the root element <Project>
    project = ET.Element("Project", {
        "Author": "Generated",
        "Name": projectName,
        "UmlVersion": "2.x",
        "Xml_structure": "simple"
    })

    # Create the <Models> container under <Project>
    models = ET.SubElement(project, "Models")

    # Add all classes from inputClasses DataFrame
    for _, row in inputClasses.iterrows():
        # Create <Class> element for each row
        ET.SubElement(models, "Class", {
            "Id": row["Class ID"],
            "Name": row["Class Name"]
        })

    # Add all relationships from inputRelations DataFrame
    relationshipContainer = ET.SubElement(models, "ModelRelationshipContainer", {
        "Id": "Relationships",
        "Name": "relationships"
    })

    for _, row in inputRelations.iterrows():
        relationshipType = row["Relationship Type"]
        fromClassId = row["From Class ID"]
        toClassId = row["To Class ID"]
        aggregation = row.get("Aggregation", None)

        if relationshipType == "Generalization":
            # Add <Generalization> element
            ET.SubElement(relationshipContainer, "Generalization", {
                "From": fromClassId,
                "To": toClassId
            })
        elif relationshipType == "Aggregation":
            # Add <Association> element with AggregationKind for aggregation
            association = ET.SubElement(relationshipContainer, "Association", {
                "From": fromClassId,
                "To": toClassId
            })
            ET.SubElement(association, "FromEnd", {
                "AggregationKind": aggregation if aggregation else "None"
            })
            ET.SubElement(association, "ToEnd", {
                "AggregationKind": "None"
            })
        elif relationshipType == "Usage":
            # Add <Usage> element
            ET.SubElement(relationshipContainer, "Usage", {
                "From": fromClassId,
                "To": toClassId
            })

    # Write the XML tree to a file
    tree = ET.ElementTree(project)
    tree.write(fileName, encoding="utf-8", xml_declaration=True)
    print(f"XML file '{fileName}' generated successfully.")
def saveXml(project: ET.Element, outputXmlPath: str):
    """
    Save the XML tree to the specified file path, creating the directory if it does not exist.

    Args:
        project (ET.Element): Root element of the XML tree to save.
        outputXmlPath (str): Path where the XML file will be saved. Defaults to PIM_M2MT_XML_FILE_PATH.
    """
    # Ensure the directory for the output file exists; create if it does not
    directory = os.path.dirname(outputXmlPath)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory '{directory}' created.")

    # Save the XML tree to the specified file
    tree = ET.ElementTree(project)
    with open(outputXmlPath, "wb") as file:
        tree.write(file, encoding="UTF-8", xml_declaration=True)
        print(f"XML file generated successfully at '{outputXmlPath}'.")
def prettify(element: ET.Element) -> str:
    """
    Return a pretty-printed XML string for the Element.

    Args:
        element (ET.Element): The XML element to prettify.

    Returns:
        str: A pretty-printed XML string for the provided element.
    """
    roughString = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(roughString)
    return reparsed.toprettyxml(indent="    ")

### building the XML shapes ###
def addStaticProjectOptions(projectInfo):
    projectOptions = ET.SubElement(projectInfo, "ProjectOptions")
    diagramOptions = ET.SubElement(projectOptions, "DiagramOptions",
                                   ActivityDiagramControlFlowDisplayOption="\\u0000",
                                   ActivityDiagramShowActionCallBehaviorOption="\\u0000",
                                   ActivityDiagramShowActivityEdgeWeight="true",
                                   ActivityDiagramShowObjectNodeType="true",
                                   ActivityDiagramShowPartitionHandle="\\u0000",
                                   AddDataStoresExtEntitiesToDecomposedDFD="\\u0002",
                                   AlignColumnProperties="true",
                                   AllowConfigShowInOutFlowButtonsInDataFlowDiagram="false",
                                   AutoGenerateRoleName="false",
                                   AutoSetAttributeType="true",
                                   AutoSetColumnType="true",
                                   AutoSyncRoleName="true",
                                   BpdAutoStretchPools="true",
                                   BpdConnectGatewayWithFlowObjectInDifferentPool="\\u0000",
                                   BpdDefaultConnectionPointStyle="\\u0001",
                                   BpdDefaultConnectorStyle="\\u0005",
                                   BpdDhowIdOption="\\u0000",
                                   BpdShowActivitiesTypeIcon="true",
                                   BusinessProcessDiagramDefaultLanguage="English",
                                   ClassVisibilityStyle="\\u0001",
                                   ConnectorLabelOrientation="\\u0000",
                                   CreateOneMessagePerDirection="true",
                                   DecisionMergeNodeConnectionPointStyle="\\u0000",
                                   DefaultAssociationEndNavigable="\\u0001",
                                   DefaultAssociationEndVisibility="\\u0000",
                                   DefaultAssociationShowFromMultiplicity="true",
                                   DefaultAssociationShowFromRoleName="true",
                                   DefaultAssociationShowFromRoleVisibility="true",
                                   DefaultAssociationShowStereotypes="true",
                                   DefaultAssociationShowToMultiplicity="true",
                                   DefaultAssociationShowToRoleName="true",
                                   DefaultAssociationShowToRoleVisibility="true",
                                   DefaultAttributeMultiplicity="false",
                                   DefaultAttributeType="",
                                   DefaultAttributeVisibility="\\u0001",
                                   DefaultClassAttributeMultiplicity="",
                                   DefaultClassAttributeMultiplicityOrdered="false",
                                   DefaultClassAttributeMultiplicityUnique="true",
                                   DefaultClassInterfaceBall="false",
                                   DefaultClassVisibility="\\u0004",
                                   DefaultColumnType="integer(10)",
                                   DefaultConnectionPointStyle="\\u0000",
                                   DefaultConnectorStyle="\\u0001",
                                   DefaultDiagramBackground="rgb(255, 255, 255)",
                                   DefaultDisplayAsRobustnessAnalysisIcon="true",
                                   DefaultDisplayAsRobustnessAnalysisIconInSequenceDiagram="true",
                                   DefaultDisplayAsStereotypeIcon="false",
                                   DefaultFontColor="rgb(0, 0, 0)",
                                   DefaultGenDiagramTypeFromScenario="\\u0000",
                                   DefaultHtmlDocFontColor="rgb(0, 0, 0)",
                                   DefaultLineJumps="\\u0000",
                                   DefaultOperationVisibility="\\u0004",
                                   DefaultParameterDirection="\\u0002",
                                   DefaultShowAttributeInitialValue="true",
                                   DefaultShowAttributeOption="\\u0001",
                                   DefaultShowClassMemberStereotype="true",
                                   DefaultShowDirection="false",
                                   DefaultShowMultiplicityConstraints="false",
                                   DefaultShowOperationOption="\\u0001",
                                   DefaultShowOperationSignature="true",
                                   DefaultShowOrderedMultiplicityConstraint="true",
                                   DefaultShowOwnedAssociationEndAsAttribute="true",
                                   DefaultShowOwner="false",
                                   DefaultShowOwnerSkipModelInFullyQualifiedOwnerSignature="true",
                                   DefaultShowReceptionOption="\\u0001",
                                   DefaultShowTemplateParameter="true",
                                   DefaultShowTypeOption="\\u0001",
                                   DefaultShowUniqueMultiplicityConstraint="true",
                                   DefaultTypeOfSubProcess="\\u0000",
                                   DefaultWrapClassMember="false",
                                   DrawTextAnnotationOpenRectangleFollowConnectorEnd="true",
                                   EnableMinimumSize="true",
                                   EntityColumnConstraintsPresentation="\\u0002",
                                   ErdIndexNumOfDigits="-1",
                                   ErdIndexPattern="{table_name}",
                                   ErdIndexPatternSyncAutomatically="true",
                                   ErdManyToManyJoinTableDelimiter="_",
                                   EtlTableDiagramFontSize="14",
                                   ExpandedSubProcessDiagramContent="\\u0001",
                                   ForeignKeyArrowHeadSize="\\u0002",
                                   ForeignKeyConnectorEndPointAssociatedColumn="false",
                                   ForeignKeyNamePattern="{reference_table_name}{reference_column_name}",
                                   ForeignKeyNamePatternCaseHandling="0",
                                   ForeignKeyRelationshipPattern="{association_name}",
                                   FractionalMetrics="true",
                                   GeneralizationSetNotation="\\u0001",
                                   GraphicAntiAliasing="true",
                                   GridDiagramFontSize="14",
                                   LineJumpSize="\\u0000",
                                   ModelElementNameAlignment="\\u0004",
                                   MultipleLineClassName="\\u0001",
                                   PaintConnectorThroughLabel="false",
                                   PointConnectorEndToCompartmentMember="true",
                                   PrimaryKeyConstraintPattern="",
                                   PrimaryKeyNamePattern="ID",
                                   RenameConstructorAfterRenameClass="\\u0000",
                                   RenameExtensionPointToFollowExtendUseCase="\\u0000",
                                   ShapeAutoFitSize="false",
                                   ShowActivationsInSequenceDiagram="true",
                                   ShowActivityStateNodeCaption="524287",
                                   ShowArtifactOption="\\u0002",
                                   ShowAssociatedDiagramNameOfInteraction="false",
                                   ShowAssociationRoleStereotypes="true",
                                   ShowAttributeGetterSetter="false",
                                   ShowBSElementCode="true",
                                   ShowClassEmptyCompartments="false",
                                   ShowColumnDefaultValue="false",
                                   ShowColumnNullable="true",
                                   ShowColumnType="true",
                                   ShowColumnUniqueConstraintName="false",
                                   ShowColumnUserType="false",
                                   ShowComponentOption="\\u0002",
                                   ShowExtraColumnProperties="true",
                                   ShowInOutFlowButtonsInDataFlowDiagram="false",
                                   ShowInOutFlowsInSubLevelDiagram="true",
                                   ShowMessageOperationSignatureForSequenceAndCommunicationDiagram="true",
                                   ShowMessageStereotypeInSequenceAndCommunicationDiagram="true",
                                   ShowNumberInCollaborationDiagram="true",
                                   ShowNumberInSequenceDiagram="true",
                                   ShowPackageNameStyle="\\u0000",
                                   ShowParameterNameInOperationSignature="true",
                                   ShowRowGridLineWithinCompClassDiagram="false",
                                   ShowRowGridLineWithinCompERD="true",
                                   ShowRowGridLineWithinORMDiagram="true",
                                   ShowSchemaNameInERD="true",
                                   ShowTransitionTrigger="\\u0000",
                                   ShowUseCaseExtensionPoint="true",
                                   ShowUseCaseID="false",
                                   SnapConnectorsAfterZoom="false",
                                   StateShowParametersOfInternalActivities="false",
                                   StateShowPrePostConditionAndBodyOfInternalActivities="true",
                                   StopTargetLifelineOnCreateDestroyMessage="\\u0002",
                                   SupportHtmlTaggedValue="false",
                                   SupportMultipleLineAttribute="true",
                                   SuppressImpliedMultiplicityForAttributeAssociationEnd="false",
                                   SyncAssociationNameWithAssociationClass="\\u0000",
                                   SyncAssociationRoleNameWithReferencedAttributeName="true",
                                   SyncDocOfInterfaceToSubClass="\\u0000",
                                   TextAntiAliasing="true",
                                   TextualAnalysisGenerateRequirementTextOption="\\u0001",
                                   TextualAnalysisHighlightOption="\\u0000",
                                   UnnamedIndexPattern="{table_name}_{column_name}",
                                   UseStateNameTab="false",
                                   WireflowDiagramDevice="0",
                                   WireflowDiagramShowActiveFlowLabel="true",
                                   WireflowDiagramTheme="0",
                                   WireflowDiagramWireflowShowPreview="true",
                                   WireflowDiagramWireflowShowScreenId="true"
                                   )

    # Add additional sub-elements such as GeneralOptions, InstantReverseOptions, etc.
    ET.SubElement(projectOptions, "GeneralOptions", ConfirmSubLevelIdWithDot="true",
                  QuickAddGlossaryTermParentModelId="default")
    ET.SubElement(projectOptions, "InstantReverseOptions", CalculateGeneralizationAndRealization="false",
                  CreateShapeForParentModelOfDraggedClassPackage="false", ReverseGetterSetter="\\u0000",
                  ReverseOperationImplementation="false", ShowPackageForNewDiagram="\\u0001",
                  ShowPackageOwner="\\u0000")
    ET.SubElement(projectOptions, "ModelQualityOptions", EnableModelQualityChecking="false")
    ormOptions = ET.SubElement(projectOptions, "ORMOptions",
                               DecimalPrecision="19",
                               DecimalScale="0",
                               ExportCommentToDatabase="true",
                               FormattedSQL="false",
                               GenerateAssociationWithAttribute="false",
                               GenerateDiagramFromORMWizards="true",
                               GetterSetterVisibility="\\u0000",
                               IdGeneratorType="native",
                               MappingFileColumnOrder="\\u0000",
                               NumericToClassType="\\u0000",
                               QuoteSQLIdentifier="\\u0000",
                               RecreateShapeWhenSync="false",
                               SyncToClassDiagramAttributeName="\\u0001",
                               SyncToClassDiagramAttributeNamePrefix="",
                               SyncToClassDiagramAttributeNameSuffix="",
                               SyncToClassDiagramClassName="\\u0000",
                               SyncToClassDiagramClassNamePrefix="",
                               SyncToClassDiagramClassNameSuffix="",
                               SyncToERDColumnName="\\u0000",
                               SyncToERDColumnNamePrefix="",
                               SyncToERDColumnNameSuffix="",
                               SyncToERDTableName="\\u0004",
                               SyncToERDTableNamePrefix="",
                               SyncToERDTableNameSuffix="",
                               SynchronizeDefaultValueToColumn="false",
                               SynchronizeName="\\u0002",
                               TablePerSubclassFKMapping="\\u0000",
                               UpperCaseSQL="true",
                               UseDefaultDecimal="true",
                               WrappingServletRequest="\\u0001")

    # Add requirementDiagramOptions in camelCase
    requirementDiagramOptions = ET.SubElement(projectOptions, "RequirementDiagramOptions",
                                              DefaultWrapMember="true",
                                              ShowAttributes="\\u0001",
                                              SupportHTMLAttribute="false")

    # Add stateCodeEngineOptions in camelCase
    stateCodeEngineOptions = ET.SubElement(projectOptions, "StateCodeEngineOptions",
                                           AutoCreateInitialStateInStateDiagram="true",
                                           AutoCreateTransitionMethods="true",
                                           DefaultInitialStateLocationX="-1",
                                           DefaultInitialStateLocationY="-1",
                                           GenerateDebugMessage="false",
                                           GenerateSample="true",
                                           GenerateTryCatch="true",
                                           Language="\\u0000",
                                           RegenerateTransitionMethods="false",
                                           SyncTransitionMethods="true")

    # Add warningOptions in camelCase
    warningOptions = ET.SubElement(projectOptions, "WarningOptions", CreateORMClassInDefaultPackage="true")

    # Add poRepository and its children in camelCase
    poRepository = ET.SubElement(projectOptions, "PORepository")
    poUserIdFormats = ET.SubElement(poRepository, "POUserIDFormats")

    # Add poUserIdFormats child elements in camelCase
    ET.SubElement(poUserIdFormats, "POUserIDFormat",
                  Digits="2",
                  Guid="false",
                  Id="RBeZzEmGAqAC8QlN",
                  LastNumericValue="0",
                  ModelType="BPMNElement",
                  Prefix="BP",
                  Suffix="")

    ET.SubElement(poUserIdFormats, "POUserIDFormat",
                  Digits="2",
                  Guid="false",
                  Id="RBeZzEmGAqAC8QlO",
                  LastNumericValue="0",
                  ModelType="Actor",
                  Prefix="AC",
                  Suffix="")

    ET.SubElement(poUserIdFormats, "POUserIDFormat",
                  Digits="3",
                  Guid="false",
                  Id="RBeZzEmGAqAC8QlQ",
                  LastNumericValue="0",
                  ModelType="Requirement",
                  Prefix="REQ",
                  Suffix="")

    ET.SubElement(poUserIdFormats, "POUserIDFormat",
                  Digits="3",
                  Guid="false",
                  Id="RBeZzEmGAqAC8QlR",
                  LastNumericValue="0",
                  ModelType="BusinessRule",
                  Prefix="BR",
                  Suffix="")

    ET.SubElement(poUserIdFormats, "POUserIDFormat",
                  Digits="-1",
                  Guid="false",
                  Id="RBeZzEmGAqAC8QlS",
                  LastNumericValue="0",
                  ModelType="BusinessProcessDiagram",
                  Prefix="",
                  Suffix="")
def addStaticDataType(models, projectAuthor):
    data_types = [
        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "k2eZzEmGAqAC8QXD", "Name": "boolean",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXE", "Name": "byte",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXF", "Name": "char",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXG", "Name": "double",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXH", "Name": "float",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXI", "Name": "int",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXJ", "Name": "long",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXK", "Name": "short",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXL", "Name": "void",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"},

        {"BacklogActivityId": "0", "Documentation_plain": "", "Id": "G2eZzEmGAqAC8QXM", "Name": "string",
         "PmAuthor": projectAuthor, "PmCreateDateTime": generateTimestamp(),
         "PmLastModified": generateTimestamp(), "QualityReason_IsNull": "true",
         "QualityScore": "-1", "UserIDLastNumericValue": "0", "UserID_IsNull": "true"}
    ]
    for data in data_types:
        ET.SubElement(models, "DataType", **data)
def addUsageStereotype(projectAuthor, models, existingIDs, idLength):
    usageStereotypeIdRef = generateId(existingIDs, idLength)
    existingIDs.add(usageStereotypeIdRef)
    ET.SubElement(models, 'Stereotype', {
        'Abstract': 'false',
        'BacklogActivityId': '0',
        'BaseType': 'Usage',
        'Documentation_plain': '',
        'IconPath_IsNull': 'true',
        'Id': usageStereotypeIdRef,
        'Leaf': 'false',
        'Name': 'use',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),
        'PmLastModified': generateTimestamp(),
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'Root': 'false',
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true'
    })
    return usageStereotypeIdRef
def addUsageRelation(projectAuthor, modelChildrenMCC, fromID, toID, usageShapeID, usageMasterIdRef,usageStereotypeIdRef):
    """
    Function to add a usage relation with sub-elements: Stereotypes and MasterView.

    Args:
        projectAuthor: The author of the project.
        modelChildrenContainer: Parent XML element under which the 'Usage' element will be added.
        fromID: The 'From' attribute for the 'Usage' element.
        toID: The 'To' attribute for the 'Usage' element.
        usageShapeID: The unique ID for the 'Usage' element.
        usageMasterIdRef: The MasterView reference ID.
        usageStereotypeIdRef: The Stereotype reference ID.
    """
    # Create the Usage element with the necessary attributes
    usage = ET.SubElement(modelChildrenMCC, 'Usage', {
        'BacklogActivityId': '0',
        'Documentation_plain': '',
        'From': fromID,
        'Id': usageShapeID,
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),  # Generate creation timestamp
        'PmLastModified': generateTimestamp(),  # Generate last modified timestamp
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'To': toID,
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
        'Visibility': 'Unspecified'
    })

    # Add the Stereotypes sub-element
    stereotypes = ET.SubElement(usage, 'Stereotypes')
    ET.SubElement(stereotypes, 'Stereotype', {
        'Idref': usageStereotypeIdRef,  # Provided stereotype ID reference
        'Name': 'use'  # Fixed name for stereotype
    })

    # Add the MasterView sub-element
    master_view = ET.SubElement(usage, 'MasterView')
    ET.SubElement(master_view, 'Usage', {
        'Idref': usageMasterIdRef  # MasterView reference ID
    })

    return modelChildrenMCC
def addUsageRelationContainer(projectAuthor, modelChildren, pimRelations, pimClasses, usageStereotypeIdRef, existingIDs, idLength):
    """
    Function to add a container of Usage relations based on the pimRelations DataFrame.

    Args:
        projectAuthor: The author of the project.
        modelChildren: Parent XML element under which the Usage elements will be added.
        pimRelations: DataFrame containing the relationship data.
        pimClasses: DataFrame or list containing the class information.
    """

    # Variable to track if the ModelRelationshipContainer has been created
    modelChildrenContainer = None
    modelChildrenMCC = None

    # Iterate through each row in the pimRelations DataFrame
    for index, row in pimRelations.iterrows():
        relationType = row["Relationship Type"]

        if relationType == 'Usage':  # Check if the relation is of type 'Usage'

            # Create the ModelRelationshipContainer only once, before adding any Usage relations
            if modelChildrenContainer is None:
                # Generate the container ID
                IDContainer = generateId(existingIDs, idLength)
                # Add the ModelRelationshipContainer to the modelChildren
                modelChildrenContainer = ET.SubElement(modelChildren, 'ModelRelationshipContainer',
                                                       BacklogActivityId="0",
                                                       Documentation_plain="",
                                                       Id=IDContainer,
                                                       Name="Usage",
                                                       PmAuthor=projectAuthor,
                                                       PmCreateDateTime=generateTimestamp(),
                                                       PmLastModified=generateTimestamp(),
                                                       QualityReason_IsNull="true",
                                                       QualityScore="-1",
                                                       UserIDLastNumericValue="0",
                                                       UserID_IsNull="true")
                modelChildrenMCC = ET.SubElement(modelChildrenContainer, 'ModelChildren')

            fromClassID = row["From Class ID"]
            toClassID = row["To Class ID"]

            # Generate a unique Shape ID
            usageShapeID = generateId(existingIDs, idLength)
            # Add the new Shape ID to the pimRelations DataFrame
            pimRelations.at[index, 'ShapeID'] = usageShapeID
            existingIDs.add(usageShapeID)

            # Generate a unique MasterView reference ID
            usageMasterIdRef = generateId(existingIDs, idLength)
            # Add the new Master ID to the pimRelations DataFrame
            pimRelations.at[index, 'MasterID'] = usageMasterIdRef
            existingIDs.add(usageMasterIdRef)
            pimRelations.at[index, 'StereotypeID'] = usageStereotypeIdRef

            # Add the usage relation to the XML
            modelChildrenMCC = addUsageRelation(projectAuthor, modelChildrenMCC, fromClassID, toClassID, usageShapeID,
                                                usageMasterIdRef, usageStereotypeIdRef)

    return modelChildren
def addAssociationRelation(projectAuthor, modelChildrenMCC, fromID, fromName, toID, toName, aggregationKind, fromEndAssociationID, fromEndQualifierID,toEndAssociationID, toEndQualifierID, associationMasterIdRef, associationShapeID):
    """
    Function to add an association/aggregation/composition relation with sub-elements: FromEnd, ToEnd, and MasterView.

    Args:
        projectAuthor: The author of the project.
        modelChildrenContainer: Parent XML element under which the 'Association' element will be added.
        fromID: The 'From' attribute for the 'Association' element.
        fromName: The name of the 'From' class.
        toID: The 'To' attribute for the 'Association' element.
        toName: The name of the 'To' class.
        aggregationKind: The type of aggregation ("None", "Shared", "Composite").
        fromEndAssociationID: The unique ID for the 'FromEnd' association element.
        fromEndQualifierID: The unique ID for the 'FromEnd' qualifier element.
        toEndAssociationID: The unique ID for the 'ToEnd' association element.
        toEndQualifierID: The unique ID for the 'ToEnd' qualifier element.
        associationMasterIdRef: The MasterView reference ID.
        associationShapeID: The unique ID for the 'Association' element.
    """
    # Create the Association element with the necessary attributes
    association = ET.SubElement(modelChildrenMCC, 'Association', {
        'Abstract': 'false',
        'BacklogActivityId': '0',
        'Derived': 'false',
        'Direction': 'From To',
        'Documentation_plain': '',
        'EndRelationshipFromMetaModelElement': fromID,
        'EndRelationshipToMetaModelElement': toID,
        'Id': associationShapeID,
        'Leaf': 'false',
        'OrderingInProfile': '-1',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),  # Generate creation timestamp
        'PmLastModified': generateTimestamp(),  # Generate last modified timestamp
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
        'Visibility': 'Unspecified'
    })

    # Add the FromEnd sub-element with the specified aggregationKind
    fromEnd = ET.SubElement(association, 'FromEnd')
    fromAssociationEnd = ET.SubElement(fromEnd, 'AssociationEnd', {
        'AggregationKind': aggregationKind,
        'BacklogActivityId': '0',
        'ConnectToCodeModel': '1',
        'DefaultValue_IsNull': 'true',
        'Derived': 'false',
        'DerivedUnion': 'false',
        'Documentation_plain': '',
        'EndModelElement': fromID,
        'Id': fromEndAssociationID,
        'JavaCodeAttributeName': '',
        'Leaf': 'false',
        'Multiplicity': 'Unspecified',
        'Navigable': 'Navigable',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),
        'PmLastModified_IsNull': 'true',
        'ProvidePropertyGetterMethod': 'false',
        'ProvidePropertySetterMethod': 'false',
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'ReadOnly': 'false',
        'Static': 'false',
        'TypeModifier': '',
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
        'Visibility': 'Unspecified'
    })
    # Add the Qualifier for the FromEnd
    qualifierEnd = ET.SubElement(fromAssociationEnd, 'Qualifier', {
        'BacklogActivityId': '0',
        'Documentation_plain': '',
        'Id': fromEndQualifierID,
        'Name': '',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),
        'PmLastModified_IsNull': 'true',
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
    })

    # Add the Type for the FromEnd <Class Idref="fromID" Name="fromName" />
    typeEnd = ET.SubElement(fromAssociationEnd, 'Type')
    ET.SubElement(typeEnd, 'Class', {
        'Idref': fromID,
        'Name': fromName
    })

    # Add the ToEnd sub-element (with no aggregation, as per example)
    toEnd = ET.SubElement(association, 'ToEnd')
    toAssociationEnd = ET.SubElement(toEnd, 'AssociationEnd', {
        'AggregationKind': 'None',
        'BacklogActivityId': '0',
        'ConnectToCodeModel': '1',
        'DefaultValue_IsNull': 'true',
        'Derived': 'false',
        'DerivedUnion': 'false',
        'Documentation_plain': '',
        'EndModelElement': toID,
        'Id': toEndAssociationID,
        'JavaCodeAttributeName': '',
        'Leaf': 'false',
        'Multiplicity': 'Unspecified',
        'Navigable': 'Navigable',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),
        'PmLastModified_IsNull': 'true',
        'ProvidePropertyGetterMethod': 'false',
        'ProvidePropertySetterMethod': 'false',
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'ReadOnly': 'false',
        'Static': 'false',
        'TypeModifier': '',
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
        'Visibility': 'Unspecified'
    })

    # Add the Qualifier for the ToEnd
    qualifierTo = ET.SubElement(toAssociationEnd, 'Qualifier', {
        'BacklogActivityId': '0',
        'Documentation_plain': '',
        'Id': toEndQualifierID,
        'Name': '',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),
        'PmLastModified_IsNull': 'true',
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
    })

    # Add the Type for the ToEnd <Class Idref="toID" Name="toName" />
    typeTo = ET.SubElement(toAssociationEnd, 'Type')
    ET.SubElement(typeTo, 'Class', {
        'Idref': toID,
        'Name': toName
    })

    # Add the MasterView sub-element
    masterView = ET.SubElement(association, 'MasterView')
    ET.SubElement(masterView, 'Association', {
        'Idref': associationMasterIdRef  # MasterView reference ID
    })

    return modelChildrenMCC
def addAssociationRelationContainer(projectAuthor, modelChildren, pimRelations, pimClasses, existingIDs, idLength):
    """
    Function to add a container of Association/Aggregation/Composition relations based on the pimRelations DataFrame.

    Args:
        projectAuthor: The author of the project.
        modelChildren: Parent XML element under which the Association elements will be added.
        pimRelations: DataFrame containing the relationship data.
        pimClasses: DataFrame or list containing the class information.
    """

    # Variable to track if the ModelRelationshipContainer has been created
    modelChildrenContainer = None
    modelChildrenMCC = None
    # Iterate through each row in the pimRelations DataFrame
    for index, row in pimRelations.iterrows():
        relationType = row["Relationship Type"]

        # Check for association, aggregation (shared), or composition (composite)
        if relationType in ['Association', 'Aggregation', 'Composition']:

            # Create the ModelRelationshipContainer only once, before adding any association relations
            if modelChildrenContainer is None:
                # Generate the container ID
                IDContainer = generateId(existingIDs, idLength)
                # Add the ModelRelationshipContainer to the modelChildren
                modelChildrenContainer = ET.SubElement(modelChildren, 'ModelRelationshipContainer',
                                                       BacklogActivityId="0",
                                                       Documentation_plain="",
                                                       Id=IDContainer,
                                                       Name="Association",
                                                       PmAuthor=projectAuthor,
                                                       PmCreateDateTime=generateTimestamp(),
                                                       PmLastModified=generateTimestamp(),
                                                       QualityReason_IsNull="true",
                                                       QualityScore="-1",
                                                       UserIDLastNumericValue="0",
                                                       UserID_IsNull="true")
                modelChildrenMCC = ET.SubElement(modelChildrenContainer, 'ModelChildren')

            fromClassID = row["From Class ID"]
            toClassID = row["To Class ID"]
            fromClassName = row["From Class Name"]
            toClassName = row["To Class Name"]

            # Generate a unique Shape ID
            associationShapeID = generateId(existingIDs, idLength)
            # Add the new Shape ID to the pimRelations DataFrame
            pimRelations.at[index, 'ShapeID'] = associationShapeID
            existingIDs.add(associationShapeID)

            # Generate a unique MasterView reference ID
            associationMasterIdRef = generateId(existingIDs, idLength)
            # Add the new Master ID to the pimRelations DataFrame
            pimRelations.at[index, 'MasterID'] = associationMasterIdRef
            existingIDs.add(associationMasterIdRef)

            # Generate IDs for Association ends and Qualifiers
            fromEndAssociationID = generateId(existingIDs, idLength)
            existingIDs.add(fromEndAssociationID)
            toEndAssociationID = generateId(existingIDs, idLength)
            existingIDs.add(toEndAssociationID)
            fromEndQualifierID = generateId(existingIDs, idLength)
            existingIDs.add(fromEndQualifierID)
            toEndQualifierID = generateId(existingIDs, idLength)
            existingIDs.add(toEndQualifierID)

            # Determine the type of aggregation for the AssociationEnd (Shared, Composite, None)
            aggregationKind = 'None'
            if relationType == 'Aggregation':
                aggregationKind = 'Shared'
            elif relationType == 'Composition':
                aggregationKind = 'Composite'

            # Add the association relation to the XML
            modelChildrenMCC = addAssociationRelation(
                projectAuthor,
                modelChildrenMCC,
                fromClassID,
                fromClassName,
                toClassID,
                toClassName,
                aggregationKind,
                fromEndAssociationID,
                fromEndQualifierID,
                toEndAssociationID,
                toEndQualifierID,
                associationMasterIdRef,
                associationShapeID
            )

    return modelChildren
def addGeneralizationRelation(projectAuthor, modelChildrenMCC, fromID, fromName, toID, toName, generalizationShapeID, generalizationMasterIdRef):
    """
    Function to add a generalization relation with sub-elements: Generalization and MasterView.

    Args:
        projectAuthor: The author of the project.
        modelChildrenMCC: Parent XML element under which the 'Generalization' element will be added.
        fromID: The 'From' class ID for the 'Generalization' element.
        fromName: The name of the 'From' class.
        toID: The 'To' class ID for the 'Generalization' element.
        toName: The name of the 'To' class.
        generalizationShapeID: The unique ID for the 'Generalization' element.
        generalizationMasterIdRef: The MasterView reference ID.
    """
    # Create the Generalization element with the necessary attributes

    generalization = ET.SubElement(modelChildrenMCC, 'Generalization', {
        'BacklogActivityId': '0',
        'ConnectToCodeModel': '1',
        'Documentation_plain': '',
        'From': fromID,
        'Id': generalizationShapeID,
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),  # Generate creation timestamp
        'PmLastModified': generateTimestamp(),  # Generate last modified timestamp
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'Substitutable': 'false',
        'To': toID,
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
        'Visibility': 'Unspecified'
    })

    # Add the MasterView sub-element
    masterView = ET.SubElement(generalization, 'MasterView')
    ET.SubElement(masterView, 'Generalization', {
        'Idref': generalizationMasterIdRef  # MasterView reference ID
    })

    return modelChildrenMCC
def addGeneralizationRelationContainer(projectAuthor, modelChildren, pimRelations, pimClasses, existingIDs, idLength):
    """
    Function to add a container of Generalization relations based on the pimRelations DataFrame.

    Args:
        projectAuthor: The author of the project.
        modelChildren: Parent XML element under which the Generalization elements will be added.
        pimRelations: DataFrame containing the relationship data.
        pimClasses: DataFrame or list containing the class information.
    """

    # Variable to track if the ModelRelationshipContainer has been created
    modelChildrenContainer = None
    modelChildrenMCC = None

    # Iterate through each row in the pimRelations DataFrame
    for index, row in pimRelations.iterrows():
        relationType = row["Relationship Type"]

        # Check for generalization relations
        if relationType == 'Generalization':

            # Create the ModelRelationshipContainer only once, before adding any generalization relations
            if modelChildrenContainer is None:
                # Generate the container ID
                IDContainer = generateId(existingIDs, idLength)
                # Add the ModelRelationshipContainer to the modelChildren
                modelChildrenContainer = ET.SubElement(modelChildren, 'ModelRelationshipContainer',
                                                       BacklogActivityId="0",
                                                       Documentation_plain="",
                                                       Id=IDContainer,
                                                       Name="Generalization",
                                                       PmAuthor=projectAuthor,
                                                       PmCreateDateTime=generateTimestamp(),
                                                       PmLastModified=generateTimestamp(),
                                                       QualityReason_IsNull="true",
                                                       QualityScore="-1",
                                                       UserIDLastNumericValue="0",
                                                       UserID_IsNull="true")
                modelChildrenMCC = ET.SubElement(modelChildrenContainer, 'ModelChildren')

            fromClassID = row["From Class ID"]
            toClassID = row["To Class ID"]
            fromClassName = row["From Class Name"]
            toClassName = row["To Class Name"]

            # Generate a unique Shape ID for the generalization
            generalizationShapeID = generateId(existingIDs, idLength)
            # Add the new Shape ID to the pimRelations DataFrame
            pimRelations.at[index, 'ShapeID'] = generalizationShapeID
            existingIDs.add(generalizationShapeID)

            # Generate a unique MasterView reference ID
            generalizationMasterIdRef = generateId(existingIDs, idLength)
            # Add the new Master ID to the pimRelations DataFrame
            pimRelations.at[index, 'MasterID'] = generalizationMasterIdRef
            existingIDs.add(generalizationMasterIdRef)

            # Add the generalization relation to the XML
            modelChildrenMCC = addGeneralizationRelation(
                projectAuthor,
                modelChildrenMCC,
                fromClassID,
                fromClassName,
                toClassID,
                toClassName,
                generalizationShapeID,
                generalizationMasterIdRef
            )

    return modelChildren
def addDependencyRelation(projectAuthor, modelChildrenMCC, fromID, toID, dependencyShapeID, dependencyMasterIdRef):
    """
    Function to add a dependency relation with sub-elements: Dependency and MasterView.

    Args:
        projectAuthor: The author of the project.
        modelChildrenMCC: Parent XML element under which the 'Dependency' element will be added.
        fromID: The 'From' attribute for the 'Dependency' element.
        toID: The 'To' attribute for the 'Dependency' element.
        dependencyShapeID: The unique ID for the 'Dependency' element.
        dependencyMasterIdRef: The MasterView reference ID.
    """
    # Create the Dependency element with the necessary attributes
    dependency = ET.SubElement(modelChildrenMCC, 'Dependency', {
        'BacklogActivityId': '0',
        'Documentation_plain': '',
        'From': fromID,
        'Id': dependencyShapeID,
        'Name': '&lt;&lt;compliant with&gt;&gt;',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),  # Generate creation timestamp
        'PmLastModified': generateTimestamp(),  # Generate last modified timestamp
        'QualityReason_IsNull': 'true',
        'QualityScore': '-1',
        'To': toID,
        'UserIDLastNumericValue': '0',
        'UserID_IsNull': 'true',
        'Visibility': 'Unspecified'
    })

    # Add the MasterView sub-element
    masterView = ET.SubElement(dependency, 'MasterView')
    ET.SubElement(masterView, 'Dependency', {
        'Idref': dependencyMasterIdRef,
        'Name': '&lt;&lt;compliant with&gt;&gt;'
    })

    return modelChildrenMCC
def addDependencyRelationContainer(projectAuthor, modelChildren, pimRelations, pimClasses, existingIDs, idLength):
    """
    Function to add a container of Dependency (CompliantWith) relations based on the pimRelations DataFrame.

    Args:
        projectAuthor: The author of the project.
        modelChildren: Parent XML element under which the Dependency elements will be added.
        pimRelations: DataFrame containing the relationship data.
        pimClasses: DataFrame or list containing the class information.
    """

    # Variable to track if the ModelRelationshipContainer has been created
    modelChildrenContainer = None
    modelChildrenMCC = None

    # Iterate through each row in the pimRelations DataFrame
    for index, row in pimRelations.iterrows():
        relationType = row["Relationship Type"]

        # Check for compliant with relations
        if relationType == 'CompliantWith':

            # Create the ModelRelationshipContainer only once, before adding any dependency relations
            if modelChildrenContainer is None:
                # Generate the container ID
                IDContainer = generateId(existingIDs, idLength)
                # Add the ModelRelationshipContainer to the modelChildren
                modelChildrenContainer = ET.SubElement(modelChildren, 'ModelRelationshipContainer',
                                                       BacklogActivityId="0",
                                                       Documentation_plain="",
                                                       Id=IDContainer,
                                                       Name="Dependency",
                                                       PmAuthor=projectAuthor,
                                                       PmCreateDateTime=generateTimestamp(),
                                                       PmLastModified=generateTimestamp(),
                                                       QualityReason_IsNull="true",
                                                       QualityScore="-1",
                                                       UserIDLastNumericValue="0",
                                                       UserID_IsNull="true")
                modelChildrenMCC = ET.SubElement(modelChildren, 'ModelChildren')

            fromClassID = row["From Class ID"]
            toClassID = row["To Class ID"]

            # Generate a unique Shape ID for the dependency
            dependencyShapeID = generateId(existingIDs, idLength)
            pimRelations.at[index, 'ShapeID'] = dependencyShapeID
            existingIDs.add(dependencyShapeID)

            dependencyMasterIdRef = generateId(existingIDs, idLength)
            pimRelations.at[index, 'MasterID'] = dependencyMasterIdRef
            existingIDs.add(dependencyMasterIdRef)

            # Add the dependency relation to the XML
            modelChildrenMCC = addDependencyRelation(
                projectAuthor,
                modelChildrenMCC,
                fromClassID,
                toClassID,
                dependencyShapeID,
                dependencyMasterIdRef
            )

    return modelChildren
def addClassElement(models, projectAuthor, pimClasses, pimRelations, existingIDs, IdLength):
    """
    Function to add Class elements based on the pimClasses DataFrame.

    Args:
        models: Parent XML element under which the 'Class' elements will be added.
        projectAuthor: The author of the project.
        pimClasses: DataFrame containing the class information.
        pimRelations: DataFrame containing the relationship data.
    """
    # Iterate through each class in pimClasses DataFrame
    for index, row in pimClasses.iterrows():
        classID = row["Class ID"]
        className = row["Class Name"]
        classIdRef = generateId(existingIDs, IdLength)
        existingIDs.add(classIdRef)
        pimClasses.at[index, 'ClassIdRef'] = classIdRef

        # Create the Class element with the necessary attributes
        classElement = ET.SubElement(models, 'Class', {
            'Abstract': 'false',
            'Active': 'false',
            'BacklogActivityId': '0',
            'BusinessKeyMutable': 'true',
            'BusinessModel': 'false',
            'ConnectToCodeModel': '1',
            'Documentation_plain': '',
            'Id': classIdRef,
            'Leaf': 'false',
            'Name': className,
            'PmAuthor': projectAuthor,
            'PmCreateDateTime': generateTimestamp(),  # Generate creation timestamp
            'PmLastModified': generateTimestamp(),  # Generate last modified timestamp
            'QualityReason_IsNull': 'true',
            'QualityScore': '-1',
            'Root': 'false',
            'UserIDLastNumericValue': '0',
            'UserID_IsNull': 'true',
            'Visibility': 'public'
        })

        # Filter relations from pimRelations that start from this class (FromSimpleRelationships)
        fromRelations = pimRelations[pimRelations['From Class ID'] == classID]

        if not fromRelations.empty:
            fromSimpleRel = ET.SubElement(classElement, 'FromSimpleRelationships')
            for _, relRow in fromRelations.iterrows():
                relType = relRow["Relationship Type"]
                relIDRef = relRow["ShapeID"]  # Assuming ShapeID is stored in pimRelations
                relName = ''  # Can be left empty unless specified

                # Depending on the relationship type, add the corresponding sub-element
                if relType == 'Generalization':
                    ET.SubElement(fromSimpleRel, 'Generalization', {'Idref': relIDRef, 'Name': relName})
                elif relType == 'Usage':
                    relIDRef = relRow["ShapeID"]  # Assuming ShapeID is stored in pimRelations
                    relName = ''  # Can be left empty unless specified
                    ET.SubElement(fromSimpleRel, 'Usage', {'Idref': relIDRef, 'Name': relName})
                elif relType == 'CompliantWith':
                    ET.SubElement(fromSimpleRel, 'Dependency',
                                  {'Idref': relIDRef, 'Name': '&lt;&lt;compliant with&gt;&gt;'})
                # Add more conditions if needed for other relationship types

        # Filter relations from pimRelations that point to this class (ToSimpleRelationships)
        toRelations = pimRelations[pimRelations['To Class ID'] == classID]

        if not toRelations.empty:
            toSimpleRel = ET.SubElement(classElement, 'ToSimpleRelationships')
            for _, relRow in toRelations.iterrows():
                relType = relRow["Relationship Type"]
                relIDRef = relRow["ShapeID"]  # Assuming ShapeID is stored in pimRelations
                relName = ''  # Can be left empty unless specified

                if relType == 'Generalization':
                    ET.SubElement(toSimpleRel, 'Generalization', {'Idref': relIDRef, 'Name': relName})

        # Add the MasterView sub-element
        masterView = ET.SubElement(classElement, 'MasterView')
        ET.SubElement(masterView, 'Class', {'Idref': classIdRef, 'Name': className})

    return models
def addClassDiagram(diagrams, projectAuthor, classDiagramID, classDiagramName):
    """
    Function to add a ClassDiagram element to the Diagrams section with all the detailed attributes.

    Args:
        diagrams: Parent XML element under which the 'ClassDiagram' element will be added.
        projectAuthor: The author of the project.
    """
    # Create the ClassDiagram element with all the specified attributes
    classDiagram = ET.SubElement(diagrams, 'ClassDiagram', {
        'AlignToGrid': 'false',
        'AutoFitShapesSize': 'false',
        'ClassFitSizeWhenShowHideMember': 'true',
        'ConnectionPointStyle': '0',
        'ConnectorLabelOrientation': '0',
        'ConnectorLineJumps': '0',
        'ConnectorLineJumpsSize': '0',
        'ConnectorModelElementNameAlignment': '4',
        'ConnectorStyle': '1',
        'DiagramBackground': 'rgb(255, 255, 255)',
        'Editable': 'true',
        'FollowDiagramParentElement': 'true',
        'GeneralizationSetNotation': '2',
        'GridColor': 'rgb(192, 192, 192)',
        'GridHeight': '10',
        'GridVisible': 'false',
        'GridWidth': '10',
        'Height': '595',
        'HideConnectorIfFromToIsHidden': '0',
        'HideEmptyTaggedValues': 'false',
        'Id': classDiagramID,
        'ImageHeight': '0',
        'ImageScale': '1.0',
        'ImageWidth': '0',
        'InitializeDiagramForCreate': 'true',
        'Maximized': 'true',
        'ModelElementNameAlignment': '4',
        'Name': classDiagramName,
        'PaintConnectorThroughLabel': '1',
        'PmAuthor': projectAuthor,
        'PmCreateDateTime': generateTimestamp(),  # Generate creation timestamp
        'PmLastModified': generateTimestamp(),  # Generate last modified timestamp
        'PointConnectorEndToCompartmentMember': 'true',
        'QualityScore': '-1',
        'RequestFitSizeWithPromptUser': 'false',
        'RequestValidateSnapToGrid': 'false',
        'ShapePresentationOption': '0',
        'ShowActivityStateNodeCaption': '524287',
        'ShowAllocatedFrom': 'true',
        'ShowAllocatedTo': 'true',
        'ShowAssociationNavigationArrows': '3',
        'ShowAttributeGetterSetter': 'false',
        'ShowAttributesCodeDetails': '2',
        'ShowAttributesPropertyModifiers': '2',
        'ShowAttributesType': '1',
        'ShowClassEmptyCompartments': '2',
        'ShowClassOwner': '2',
        'ShowClassReferencedAttributes': 'true',
        'ShowColorLegend': 'false',
        'ShowConnectorLegend': 'false',
        'ShowConnectorName': '0',
        'ShowConstraints': 'false',
        'ShowDefaultPackage': 'true',
        'ShowEllipsisForUnshownClassMembers': '2',
        'ShowInformationItemOption': '2',
        'ShowOperationsCodeDetails': '2',
        'ShowOperationsParameters': '1',
        'ShowOperationsReturnType': '1',
        'ShowPMAuthor': 'false',
        'ShowPMDifficulty': 'false',
        'ShowPMDiscipline': 'false',
        'ShowPMIteration': 'false',
        'ShowPMPhase': 'false',
        'ShowPMPriority': 'false',
        'ShowPMStatus': 'false',
        'ShowPMVersion': 'false',
        'ShowPackageNameStyle': '0',
        'ShowPackageOwner': '2',
        'ShowParametersCodeDetails': '2',
        'ShowShapeLegend': 'false',
        'ShowShapeStereotypeIconName': 'true',
        'ShowStereotypes': 'true',
        'ShowTaggedValues': 'false',
        'ShowTemplateInfoOfGeneralizationAndRealization': 'false',
        'SuppressImplied1MultiplicityForAttributeAndAssociationEnd': 'false',
        'TeamworkCreateDateTime': '0',
        'TrimmedHeight': '0',
        'TrimmedWidth': '0',
        'Width': '1255',
        'X': '0',
        'Y': '0',
        'ZoomRatio': '0.9',
        "_globalPaletteOption": "true",
        "documentation": """&lt;html&gt;&#13;&#10;&lt;head&gt;&#13;&#10;&lt;style type=&quot;text/css&quot;&gt;&#10;&lt;!--&#10; body { color: #000000; font-family: Dialog; font-size: 12px }&#10;--&gt;&#10;&lt;/style&gt;&#13;&#10;&lt;/head&gt;&#13;&#10;&lt;body&gt;&#13;&#10;&lt;p&gt;&#13;&#10;&lt;/p&gt;&#13;&#10;&lt;/body&gt;&#13;&#10;&lt;/html&gt;"""
    })

    return classDiagram
def generateXYValues(pimClasses, pimRelations):
    """
    Function to generate unique X, Y, and Z values for the classes based on relationships in pimRelations.
    Classes that are connected should be placed near each other, but still have unique positions.

    Args:
        pimClasses: DataFrame containing class details.
        pimRelations: DataFrame containing relationships between classes.

    Returns:
        Updated pimClasses with X, Y, and Z values.
    """
    # Parameters for the grid spacing
    xSpacing = 200  # Horizontal space between classes
    ySpacing = 100  # Vertical space between rows of classes
    xOffset = 50  # Slight offset to avoid exact overlapping
    yOffset = 50  # Slight offset for Y values for better separation

    # Initialize starting positions and ZOrder
    xPos = 100  # Starting X coordinate
    yPos = 100  # Starting Y coordinate
    zOrderValue = 4  # Starting Z-order value

    # Track placed classes and their positions
    placedClasses = {}

    # Iterate over each class and assign positions
    for index, classRow in pimClasses.iterrows():
        classId = classRow['ClassIdRef']

        # Check if the class has already been placed (i.e., already has X, Y values)
        if classId in placedClasses:
            continue  # Skip already placed classes

        # Assign the initial position for the class if not already placed
        pimClasses.at[index, 'X'] = xPos
        pimClasses.at[index, 'Y'] = yPos
        pimClasses.at[index, 'ZOrder'] = zOrderValue
        placedClasses[classId] = (xPos, yPos)

        # Increment ZOrder for the next class
        zOrderValue += 1

        # Fetch all relationships for this class (both as a source and destination)
        relatedClasses = pimRelations[(pimRelations['From Class ID'] == classId) |
                                      (pimRelations['To Class ID'] == classId)]

        # For each related class, place it near the current class
        for _, relation in relatedClasses.iterrows():
            relatedClassId = relation['To Class ID'] if relation['From Class ID'] == classId else relation[
                'From Class ID']

            # Check if the related class has already been placed
            if relatedClassId in placedClasses:
                continue  # Skip if the related class is already placed

            # Slightly adjust X and Y to place the related class nearby but not overlapping
            newXPos = xPos + xOffset
            newYPos = yPos + yOffset

            # Find the index of the related class in pimClasses
            relatedClassIndex = pimClasses[pimClasses['ClassIdRef'] == relatedClassId].index[0]

            # Set the X, Y, and ZOrder values for the related class
            pimClasses.at[relatedClassIndex, 'X'] = newXPos
            pimClasses.at[relatedClassIndex, 'Y'] = newYPos
            pimClasses.at[relatedClassIndex, 'ZOrder'] = zOrderValue

            # Track the new class placement
            placedClasses[relatedClassId] = (newXPos, newYPos)

            # Increment ZOrder and X/Y for the next related class
            zOrderValue += 1
            xOffset += xSpacing
            yOffset += ySpacing

        # Update X and Y for the next group of unrelated classes (do not reset X/Y)
        xPos += xSpacing
        yPos += ySpacing

    return pimClasses
def addClassShapes(shapes, pimClasses, pimRelations):
    """
    Function to add class shapes to the ClassDiagram section of the XML.

    Args:
        shapes: The parent XML element 'Shapes' where class shapes will be added.
        pimClasses: DataFrame containing class details such as ClassIdRef, Name, and MetaModelElement.
    """

    pimClasses = generateXYValues(pimClasses, pimRelations)
    # Iterate over each row in the pimClasses DataFrame
    for index, row in pimClasses.iterrows():
        classIdRef = row['ClassIdRef']
        className = row['Class Name']
        xValue = row['X']
        yValue = row['Y']
        zOrderValue = row['ZOrder']

        # Add the Class shape for each class
        classShape = ET.SubElement(shapes, 'Class', {
            "AttributeSortType": "0",
            "Background": "rgb(245, 245, 245)",
            "ConnectToPoint": "true",
            "ConnectionPointType": "2",
            "CoverConnector": "false",
            "CreatorDiagramType": "ClassDiagram",
            "DisplayAsRobustnessAnalysisIcon": "true",
            "EnumerationLiteralSortType": "0",
            "Foreground": "rgb(102, 102, 102)",
            "Height": "40",  # Height is fixed for all classes
            "Id": classIdRef,  # The ID from pimClasses
            "InterfaceBall": "false",
            "KShDrOp": "false",
            "KSwCsMbSt": "true",
            "LShCmMl": "false",
            "LshRfAts": "0",
            "MShDrAt": "false",
            "MSwTpPts": "true",
            "MetaModelElement": classIdRef,  # Same as ClassIdRef
            "Model": classIdRef,  # Same as ClassIdRef
            "ModelElementNameAlignment": "1",
            "Name": className,  # The class name from pimClasses
            "OperationSortType": "0",
            "OverrideAppearanceWithStereotypeIcon": "true",
            "ParentConnectorDTheta": "0.0",
            "ParentConnectorHeaderLength": "40",
            "ParentConnectorLineLength": "10",
            "PresentationOption": "4",
            "PrimitiveShapeType": "0",
            "ReceptionSortType": "0",
            "RequestDefaultSize": "false",
            "RequestFitSize": "false",
            "RequestFitSizeFromCenter": "false",
            "RequestResetCaption": "false",
            "RequestResetCaptionFitWidth": "false",
            "RequestResetCaptionSize": "false",
            "RequestSetSizeOption": "0",
            "Selectable": "true",
            "ShowAllocatedFrom": "0",
            "ShowAllocatedTo": "0",
            "ShowAttributeType": "1",
            "ShowAttributesCodeDetails": "0",
            "ShowAttributesPropertyModifiers": "0",
            "ShowAttributesType": "0",
            "ShowClassMemberConstraints": "true",
            "ShowEllipsisForUnshownMembers": "0",
            "ShowEmptyCompartments": "0",
            "ShowEnumerationLiteralType": "1",
            "ShowInitialAttributeValue": "true",
            "ShowOperationParameterDirection": "false",
            "ShowOperationProperties": "false",
            "ShowOperationRaisedExceptions": "false",
            "ShowOperationSignature": "true",
            "ShowOperationTemplateParameters": "false",
            "ShowOperationType": "1",
            "ShowOperationsCodeDetails": "0",
            "ShowOperationsParameters": "0",
            "ShowOperationsReturnType": "0",
            "ShowOwnerOption": "3",
            "ShowParameterNameInOperationSignature": "true",
            "ShowParametersCodeDetails": "0",
            "ShowReceptionType": "1",
            "ShowStereotypeIconName": "0",
            "ShowTypeOption": "0",
            "SuppressImplied1MultiplicityForAttribute": "0",
            "VisibilityStyle": "1",
            "Width": "163",  # Fixed width for all classes
            "WpMbs": "false",
            "X": str(xValue),  # X value from pimClasses
            "Y": str(yValue),  # Y value from pimClasses
            "ZOrder": str(zOrderValue)  # Z value from pimClasses
        })

        # Add additional sub-elements such as ElementFont, Line, Caption, FillColor, etc.
        ET.SubElement(classShape, "ElementFont", {
            "Color": "rgb(0, 0, 0)",
            "Name": "Dialog",
            "Size": "14",
            "Style": "0"
        })

        line = ET.SubElement(classShape, "Line", {
            "Cap": "0",
            "Color": "rgb(102, 102, 102)",
            "Transparency": "0",
            "Weight": "1.0"
        })
        ET.SubElement(line, "Stroke")

        ET.SubElement(classShape, "Caption", {
            "Height": "19",
            "InternalHeight": "-2147483648",
            "InternalWidth": "-2147483648",
            "Side": "FreeMove",
            "Visible": "true",
            "Width": "164",
            "X": "0",
            "Y": "0"
        })

        ET.SubElement(classShape, "FillColor", {
            "Color": "rgb(245, 245, 245)",
            "Style": "1",
            "Transparency": "0",
            "Type": "1"
        })

        ET.SubElement(classShape, "CompartmentFont", {
            "Value": "none"
        })

    return shapes
def addSubElementsToConnector(connector_element, relation_type, from_x, from_y, to_x, to_y):
    """
    Function to add sub-elements like ElementFont, Line, Caption, Points, and
    specific elements for Association, Generalization, Usage, and Dependency connectors.

    Args:
        connector_element: The XML element for the connector.
        relation_type: The type of relationship (Generalization, Association, Usage, Dependency).
        from_x, from_y: Coordinates of the "From" class.
        to_x, to_y: Coordinates of the "To" class.
    """
    # Add common sub-elements: ElementFont, Line, and Caption
    ET.SubElement(connector_element, "ElementFont", {
        "Color": "rgb(0, 0, 0)",
        "Name": "Dialog",
        "Size": "16" if relation_type != 'Association' else "12",  # Different font size for association
        "Style": "0"
    })

    line = ET.SubElement(connector_element, "Line", {
        "Cap": "0",
        "Color": "rgb(0, 0, 0)",
        "Transparency": "0",
        "Weight": "1.0"
    })
    ET.SubElement(line, "Stroke")

    caption_x = (from_x + to_x) / 2
    caption_y = (from_y + to_y) / 2
    ET.SubElement(connector_element, "Caption", {
        "Height": "0" if relation_type != 'Dependency' else "21",  # For Dependency, Caption height is different
        "InternalHeight": "-2147483648",
        "InternalWidth": "-2147483648",
        "Side": "None",
        "Visible": "true",
        "Width": "20" if relation_type != 'Dependency' else "160",  # For Dependency, Caption width is different
        "X": str(caption_x),
        "Y": str(caption_y + 20) if relation_type == 'Dependency' else str(caption_y)
    })

    # Add Points to describe the path of the connector between classes
    points = ET.SubElement(connector_element, "Points")
    ET.SubElement(points, "Point", {"X": str(from_x + 20), "Y": str(from_y + 50)})  # Starting point near "From" class
    ET.SubElement(points, "Point", {"X": str(to_x), "Y": str(to_y - 20)})  # Ending point near "To" class

    # Additional sub-elements based on the relation type
    if relation_type == 'Association':
        # Add specific sub-elements for Association
        ET.SubElement(connector_element, "MultiplicityBRectangle", {
            "Height": "16",
            "Width": "39",
            "X": str(to_x + 50),
            "Y": str(to_y + 30)
        })

        roleB = ET.SubElement(connector_element, "RoleB")
        ET.SubElement(roleB, "MultiplicityCaption", {
            "Height": "16",
            "Width": "39",
            "X": str(to_x + 50),
            "Y": str(to_y + 30)
        })

    elif relation_type == 'Usage':
        # Add specific sub-elements for Usage (mostly similar to Generalization)
        # No special elements for Usage beyond the common ones
        pass

    elif relation_type == 'Dependency':
        # Add specific sub-elements for Dependency
        pass  # Dependency only requires the standard elements
def addConnectorsForRelations(connectors, pimRelations, pimClasses):
    """
    Function to add connectors for relations in the ClassDiagram section, including Dependency relations.

    Args:
        connectors: Class diagram XML element to which the connectors will be added.
        pimRelations: DataFrame containing relationships between classes.
        pimClasses: DataFrame containing class details like ClassIdRef.
    """

    zOrderCounter = 100  # Start ZOrder for connectors

    # Iterate over each relation in pimRelations DataFrame
    for _, relation in pimRelations.iterrows():
        from_class_id = relation['From Class ID']
        to_class_id = relation['To Class ID']
        relation_type = relation['Relationship Type']
        shape_id = relation['ShapeID']

        # Get X, Y positions of From and To classes from pimClasses
        from_class_position = pimClasses[pimClasses['Class ID'] == from_class_id][['X', 'Y']].values[0]
        to_class_position = pimClasses[pimClasses['Class ID'] == to_class_id][['X', 'Y']].values[0]

        from_x, from_y = from_class_position
        to_x, to_y = to_class_position

        # Generate the midpoint for connector X, Y values
        x_value = (from_x + to_x) / 2
        y_value = (from_y + to_y) / 2
        z_order_value = zOrderCounter
        zOrderCounter += 1

        from_class_id = pimClasses[pimClasses['Class ID'] == from_class_id]['ClassIdRef'].values[0]
        to_class_id = pimClasses[pimClasses['Class ID'] == to_class_id]['ClassIdRef'].values[0]
        # Common attributes for all connectors
        common_attributes = {
            "Background": "rgb(255, 255, 255)" if relation_type == 'Generalization' else "rgb(122, 207, 245)",
            # Different colors for generalization vs others
            "ConnectorLabelOrientation": "4",
            "ConnectorLineJumps": "4",
            "ConnectorStyle": "Follow Diagram",
            "CreatorDiagramType": "ClassDiagram",
            "Foreground": "rgb(0, 0, 0)",
            "From": from_class_id,
            "FromConnectType": "0",
            "FromPinType": "1",
            "FromShapeXDiff": "0",
            "FromShapeYDiff": "0",
            "Height": str(abs(from_y - to_y)),
            "Id": shape_id,
            "MetaModelElement": shape_id,
            "Model": shape_id,
            "ModelElementNameAlignment": "9",
            "PaintThroughLabel": "2",
            "RequestRebuild": "false",
            "Selectable": "true",
            "ShowConnectorName": "2",
            "To": to_class_id,
            "ToConnectType": "0",
            "ToPinType": "1",
            "ToShapeXDiff": "0",
            "ToShapeYDiff": "0",
            "UseFromShapeCenter": "true",
            "UseToShapeCenter": "true",
            "Width": str(abs(from_x - to_x)),
            "X": str(x_value),
            "Y": str(y_value),
            "ZOrder": str(z_order_value)
        }

        # Create the connector element based on the relation type
        if relation_type == 'Generalization':
            connector_element = ET.SubElement(connectors, 'Generalization', common_attributes)
        elif relation_type == 'Aggregation' or relation_type == 'Association':
            connector_element = ET.SubElement(connectors, 'Association', common_attributes)
        elif relation_type == 'Usage':
            connector_element = ET.SubElement(connectors, 'Usage', common_attributes)
        elif relation_type == 'Dependency':  # Add Dependency relation
            common_attributes["Name"] = "&lt;&lt;compliant with&gt;&gt;"  # Name field for Dependency relation
            connector_element = ET.SubElement(connectors, 'Dependency', common_attributes)

        # Add the sub-elements like ElementFont, Line, Caption, Points, and specific elements for each relation type
        addSubElementsToConnector(connector_element, relation_type, from_x, from_y, to_x, to_y)

    return connectors
def createTransformedXML(OutputXMLPath: str, projectAuthor: str, projectName: str, classDiagramName: str, inputClasses: pd.DataFrame, inputRelations: pd.DataFrame):
    project = ET.Element("Project", Author=projectAuthor,
                         CommentTableSortAscending="false",
                         CommentTableSortColumn="Date Time",
                         DocumentationType="html",
                         ExportedFromDifferentName="false",
                         ExporterVersion="16.1.1",
                         Name=projectName,
                         TextualAnalysisHighlightOptionCaseSensitive="false",
                         UmlVersion="2.x",
                         Xml_structure="simple")
    projectInfo = ET.SubElement(project, "ProjectInfo")
    logicalView = ET.SubElement(projectInfo, "LogicalView")
    addStaticProjectOptions(projectInfo)
    models = ET.SubElement(project, 'Models')
    addStaticDataType(models, projectAuthor)
    ### MODEL RELATIONS CONTAINER ####
    existingIDs = getExistingIds(inputClasses)
    IdLength = getIdLength(inputClasses)

    usageStereotypeIdRef = addUsageStereotype(projectAuthor, models, existingIDs, IdLength)
    IDContainer = generateId(existingIDs, IdLength)
    relationContainer = ET.SubElement(models, 'ModelRelationshipContainer',
                                      BacklogActivityId="0",
                                      Documentation_plain="",
                                      Id=IDContainer,
                                      Name="relationships",
                                      PmAuthor=projectAuthor,
                                      PmCreateDateTime="2024-09-05T12:10:58.354",
                                      PmLastModified="2024-09-09T10:55:31.670",
                                      QualityReason_IsNull="true",
                                      QualityScore="-1",
                                      UserIDLastNumericValue="0",
                                      UserID_IsNull="true")

    modelChildren = ET.SubElement(relationContainer, 'ModelChildren')
    modelChildren = addUsageRelationContainer(projectAuthor, modelChildren, inputRelations, inputClasses, usageStereotypeIdRef,existingIDs, IdLength)
    modelChildren = addAssociationRelationContainer(projectAuthor, modelChildren, inputRelations, inputClasses, existingIDs, IdLength)
    modelChildren = addGeneralizationRelationContainer(projectAuthor, modelChildren, inputRelations, inputClasses, existingIDs, IdLength)
    modelChildren = addDependencyRelationContainer(projectAuthor, modelChildren, inputRelations, inputClasses, existingIDs, IdLength)

    #################################
    ### CLASS  ####
    models = addClassElement(models, projectAuthor, inputClasses, inputRelations, existingIDs, IdLength)
    ###############

    ############## DIAGRAM #############
    diagrams = ET.SubElement(project, 'Diagrams')
    classDiagramID = generateId(existingIDs, IdLength)
    classDiagram = addClassDiagram(diagrams, projectAuthor, classDiagramID, classDiagramName)
    shapes = ET.SubElement(classDiagram, 'Shapes')
    shapes = addClassShapes(shapes, inputClasses, inputRelations)
    connectors = ET.SubElement(classDiagram, 'Connectors')
    connectors = addConnectorsForRelations(connectors, inputRelations, inputClasses)
    #formattedXML = prettify(project)
    saveXml(project, OutputXMLPath)
    #print(formattedXML)

CIM_VP_XML_FILE_PATH = "./MDAModelingLevels/01.CIM/VP_GENERATED_XML/project.xml"
CIM_IMPORTED_CLASSES_FILE_PATH = "./TransformationResults/Classes/imported_cimclasses.csv"
CIM_IMPORTED_RELATIONS_FILE_PATH = "./TransformationResults/Relations/imported_cimrelations.csv"

# Meta Class representing the Physical Twin that the Digital Twin seeks to replicate.
CIM_REAL_TWIN_CLASS_NAME = "RealCity"
#Meta Class abstracting entities in the Physical Twin to be digitally replicated.
PHYSICAL_ENTITY_CLASS_NAME="PhysicalEntity"
#Meta Class abstracting temporal entities in the Physical Twin.
TEMPORAL_ENTITY_CLASS_NAME="TemporalEntity"
#Meta Class abstracting sensor entities in the Physical Twin.
SENSOR_ENTITY_CLASS_NAME="Sensor"
#Meta Class abstracting actuator entities in the Physical Twin.
ACTUATOR_ENTITY_CLASS_NAME="Actuator"

PIM_M2MT_XML_FILE_PATH = "./MDAModelingLevels/02.PIM/M2MT_GENERATED_XML/pim.xml"
PIM_VP_XML_FILE_PATH = "./MDAModelingLevels/02.PIM/VP_GENERATED_XML/project.xml"
PIM_PROJECT_NAME = "PlaformIndependentModel"
PIM_PROJECT_AUTHOR = "PIMAuthor"
PIM_CLASS_DIAGRAM_NAME = "BolognaMobilityDigitalTwin"
PIM_GENERATED_CLASSES_FILE_PATH = "./TransformationResults/Classes/generated_pimclasses.csv"
PIM_GENERATED_RELATIONS_FILE_PATH = "./TransformationResults/Relations/generated_pimrelations.csv"

PIM_DIGITAL_RELATED_CLASS_NAME = "DigitalRepresentation"
PIM_DIGITAL_MODEL_RELATED_CLASS_NAME = "DigitalModel"
PIM_MODEL_MANAGER_CLASS_NAME = "DigitalModelManager"
PIM_TWIN_MANAGER_CLASS_NAME = "DigitalTwinManager"


PSM_M2MT_XML_FILE_PATH = "./MDAModelingLevels/03.PSM/M2MT_GENERATED_XML/psm.xml"
PSM_VP_XML_FILE_PATH = "./MDAModelingLevels/03.PSM/VP_GENERATED_XML/project.xml"
PSM_PROJECT_NAME = "PlatformSpecificModel"
PSM_PROJECT_AUTHOR = "PSMAuthor"
PSM_CLASS_DIAGRAM_NAME = "FiwareandSumoBolognaMobilityDigitalTwin"
PSM_GENERATED_CLASSES_FILE_PATH = "./TransformationResults/Classes/generated_psmclasses.csv"
PSM_GENERATED_RELATIONS_FILE_PATH = "./TransformationResults/Relations/generated_psmrelations.csv"
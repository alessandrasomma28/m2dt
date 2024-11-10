from TransformationRules.constants import CIM_XML_FILE_PATH, CIM_IMPORTED_CLASSES_FILE_PATH, CIM_IMPORTED_RELATIONS_FILE_PATH, PIM_XML_FILE_PATH, PIM_PROJECT_NAME, PIM_CLASS_DIAGRAM_NAME, PIM_PROJECT_AUTHOR, PIM_GENERATED_CLASSES_FILE_PATH, PIM_GENERATED_RELATIONS_FILE_PATH
from TransformationRules.xmlutils import XMLUMLParser, saveToCsv, createTransformedXML
from TransformationRules.CIM2PIM.cim2pim import cim2pimTransformation

def main():

    ############ CIM TO PIM TRANSFORMATION STEP ############

    #1. Read classes and relations from VP_GENERATED_XML CIM
    imported_cimClasses, imported_cimRelations = XMLUMLParser(CIM_XML_FILE_PATH)
    #print(imported_cimClasses)
    #print(imported_cimRelations)
    saveToCsv(imported_cimClasses, imported_cimRelations, CIM_IMPORTED_CLASSES_FILE_PATH, CIM_IMPORTED_RELATIONS_FILE_PATH)

    #2. Apply CIM2PIM transformation rules
    generated_pimClasses, generated_pimRelations = cim2pimTransformation(cimClasses=imported_cimClasses, cimRelations=imported_cimRelations)
    #print(generated_pimClasses)
    #print(generated_pimRelations)
    saveToCsv(generated_pimClasses, generated_pimRelations, PIM_GENERATED_CLASSES_FILE_PATH, PIM_GENERATED_RELATIONS_FILE_PATH)

    #3. Convert the PIM classes and relations into XML file in PIM/M2MT_GENERATED_XML
    createTransformedXML(PIM_XML_FILE_PATH, PIM_PROJECT_AUTHOR, PIM_PROJECT_NAME, PIM_CLASS_DIAGRAM_NAME, generated_pimClasses, generated_pimRelations)

    ############ PIM TO PSM TRANSFORMATION STEP ############

    # 1. Read classes and relations from VP_GENERATED_XML PIM
    # imported pim classes, imported pim relations

    # 2. Apply PIM2PSM transformation rules

    # 3. Convert the PSM classes and relations into XML file in PSM/M2MT_GENERATED_XML






if __name__ == "__main__":
        main()
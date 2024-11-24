from TransformationRules.constants import (CIM_VP_XML_FILE_PATH, CIM_IMPORTED_CLASSES_FILE_PATH,
                                           CIM_IMPORTED_RELATIONS_FILE_PATH, PIM_M2MT_XML_FILE_PATH,
                                           PIM_PROJECT_NAME, PIM_CLASS_DIAGRAM_NAME, PIM_PROJECT_AUTHOR,
                                           PIM_GENERATED_CLASSES_FILE_PATH, PIM_GENERATED_RELATIONS_FILE_PATH,
                                           PIM_VP_XML_FILE_PATH, PSM_VP_XML_FILE_PATH, PSM_PROJECT_NAME,
                                           PSM_M2MT_XML_FILE_PATH, PSM_PROJECT_AUTHOR, PSM_CLASS_DIAGRAM_NAME,
                                           PSM_GENERATED_RELATIONS_FILE_PATH, PSM_GENERATED_CLASSES_FILE_PATH)
from TransformationRules.xmlutils import SourceXMLParser, saveToCsv, TargetXMLCreator
from TransformationRules.CIM2PIM.cim2pim import cim2pimTransformation
from TransformationRules.PIM2PSM.pim2psm import pim2psmTransformation

def main():

    ############ CIM TO PIM TRANSFORMATION STEP ############

    #1. Read classes and relations from VP_GENERATED_XML CIM
    imported_cimClasses, imported_cimRelations = SourceXMLParser(CIM_VP_XML_FILE_PATH)
    #print(imported_cimClasses)
    #print(imported_cimRelations)
    saveToCsv(imported_cimClasses, imported_cimRelations, CIM_IMPORTED_CLASSES_FILE_PATH, CIM_IMPORTED_RELATIONS_FILE_PATH)

    #2. Apply CIM2PIM transformation rules
    generated_pimClasses, generated_pimRelations = cim2pimTransformation(cimClasses=imported_cimClasses, cimRelations=imported_cimRelations)
    #print(generated_pimClasses)
    #print(generated_pimRelations)
    saveToCsv(generated_pimClasses, generated_pimRelations, PIM_GENERATED_CLASSES_FILE_PATH, PIM_GENERATED_RELATIONS_FILE_PATH)

    #3. Convert the PIM classes and relations into XML file in PIM/M2MT_GENERATED_XML
    TargetXMLCreator(PIM_M2MT_XML_FILE_PATH, PIM_PROJECT_AUTHOR, PIM_PROJECT_NAME, PIM_CLASS_DIAGRAM_NAME,
                     generated_pimClasses, generated_pimRelations)

    ############ PIM TO PSM TRANSFORMATION STEP ############

    # 1. Read classes and relations from VP_GENERATED_XML PIM
    ###imported_pimClasses, imported_pimRelations = XMLUMLParser(PIM_VP_XML_FILE_PATH)

    # 2. Apply PIM2PSM transformation rules
    generated_psmClasses, generated_psmRelations = pim2psmTransformation(generated_pimClasses, generated_pimRelations)
    print(generated_psmClasses, generated_psmRelations)
    saveToCsv(generated_psmClasses, generated_psmRelations, PSM_GENERATED_CLASSES_FILE_PATH,
              PSM_GENERATED_RELATIONS_FILE_PATH)
    # 3. Convert the PSM classes and relations into XML file in PSM/M2MT_GENERATED_XML
    TargetXMLCreator(PSM_M2MT_XML_FILE_PATH, PSM_PROJECT_AUTHOR, PSM_PROJECT_NAME, PSM_CLASS_DIAGRAM_NAME,
                     generated_psmClasses, generated_psmRelations)




if __name__ == "__main__":
        main()
from TransformationRules.constants import CIM_XML_FILE_PATH, CIM_CLASSES_FILE_PATH, CIM_RELATIONS_FILE_PATH
from TransformationRules.utils import XMLUMLParser, saveToCsv

def main():
    ## 1. Read classes and relations from VP_GENERATED_XML CIM
    imported_cimClasses, imported_cimRelations = XMLUMLParser(CIM_XML_FILE_PATH)
    print(imported_cimClasses)
    print(imported_cimRelations)
    saveToCsv(imported_cimClasses, imported_cimRelations, CIM_CLASSES_FILE_PATH, CIM_RELATIONS_FILE_PATH)

    ## 2. Apply CIM2PIM transformation rules

    ## 4. Convert the PIM classes and relations in VP_GENERATED_XML of Bologna Digital Twin Domain Model (PIM)




if __name__ == "__main__":
        main()
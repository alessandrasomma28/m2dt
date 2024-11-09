from TransformationRules.constants import CIM_XML_FILE_PATH
from TransformationRules.utils import XMLUMLParser

def main():
    ## 1. Import the XML of Bologna Mobility Domain Model (CIM)
    cimClasses, cimRelations = XMLUMLParser(CIM_XML_FILE_PATH)
    ## 2. Read classes and relations from XML CIM

    ## 3. Apply CIM2PIM transformation rules

    ## 4. Convert the PIM classes and relations in XML of Bologna Digital Twin Domain Model (PIM)




if __name__ == "__main__":
        main()
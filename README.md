# M2DT: Model-driven Mobility Digital Twin Tool
![Python Badge](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/alessandrasomma28/MoDT-M2M-TT/refs/heads/main/Images/Badges/pythonb.json&label=Python&query=$.python.version&color=blue&cacheSeconds=60&logo=python)
![License](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/alessandrasomma28/MoDT-M2M-TT/refs/heads/main/Images/Badges/licenseb.json&label=License&query=$.license.version&color=orange&cacheSeconds=60&logo=GNU)
![Repo Size](https://img.shields.io/github/repo-size/alessandrasomma28/MoDT-M2M-TT?logo=github)

**M2DT** is the *Model-driven Mobility Digital Twin Tool* used in the *Model-Driven 
Architecture* (MDA) approach for developing *Mobility Digital Twins* (MoDT). It automates **Model-to-Model (M2M) 
transformations**, specifically transforming models from the *Computational Independent Model* (CIM) to the 
*Platform Independent Model* (PIM), and from the *PIM* to the *Platform Specific Model* (PSM).

The M2DT process, illustrated in Figure 1, comprises four distinct steps represented by rounded boxes. Each 
step produces an output, indicated by notes in the diagram, serving as input for the subsequent step.

<div align="center">
  <img src="Images/m2mprocesstool.png" alt="M2M Tool Image" width="700"/>
  <p><b>Figure 1:</b> M2DT. </p>
</div>

The process begins with step *M2M.1*, where the source model is converted into the eXtensible Markup Language (XML) format 
using the [**Visual Paradigm**](https://www.visual-paradigm.com/) (VP) modeling tool. 
In step *M2M.2*, the custom-built **SourceXMLParser** tool (located in [**xmlutils.py**](TransformationRules/xmlutils.py))
processes the XML source model. It extracts the elements and relationships of the imported UML Class Diagram for 
subsequent transformation.

Step *M2M.3* applies transformation rules to convert the extracted source elements and relationships into their  
corresponding target elements and relationships. If the transformation being performed is **CIM-to-PIM**, 
the **cim2pimtransformation** tool (located in [**cim2pim.py**](TransformationRules/CIM2PIM/cim2pim.py)) is used. 
For **PIM-to-PSM** transformations, the **pim2psmtransformation** tool (located in [**pim2psm.py**](TransformationRules/PIM2PSM/pim2psm.py)) 
is utilized.

Finally, in step *M2M.4*, the target elements and relationships are organized into the XML format 
using the **TargetXMLCreator** tool, also available in [**xmlutils.py**](TransformationRules/xmlutils.py)
This XML output enables import into Visual Paradigm or other modeling tools for visualizing the resulting class diagrams.


## MoDT-M2M-TT Repository structure
The repository is organized to facilitate the execution of the *MoDT-M2M-TT* tool, providing clear directories for input 
models, transformation logic, and supporting utilities. Below is a detailed breakdown of the repository structure:

```plaintext
├── MDAModelinLevels
│   ├── 01.CIM                # Directory for storing the CIM representing the source model of the entire process.
│   │   └── VP_GENERATED_XML  # Directory for storing the CIM exported in XML format from Visual Paradigm (VP).
│   ├── 02.PIM                # Directory for storing the PIM model generated by the transformation process.
│   │   └── M2MT_GENERATED_XML # Contains the PIM model created after M2M transformation on the CIM.
│   │   └── VP_GENERATED_XML  # (Optional) Stores the PIM exported in XML format from VP.
│   ├── 03.PSM                # Directory for storing the PSM model generated by the transformation process.
│   │   └── M2MT_GENERATED_XML # Contains the PSM model created after M2M transformation on the PIM.
│   │   └── VP_GENERATED_XML  # (Optional) Stores the PSM exported in XML format from VP.
│   ├── 04.ISM                # Directory for storing ISM code artifacts (Python modules) generated after Model-To-Text transformations.
│   │                           Note: This step is executed externally to the MoDT-M2M-TT tool.
│
├── TransformationRules
│   ├── constants.py          # Defines constants such as file paths and transformation configurations.
│   ├── xmlutils.py           # Implements the SourceXMLParser and TargetXMLCreator tools for parsing and generating XML.
│   ├── transformationutils.py # Contains utilities shared between CIM2PIM and PIM2PSM transformations.
│   ├── CIM2PIM               # Directory defining the 8 transformation rules and logic for CIM to PIM.
│   │   └── cim2pim.py        # Implements the CIM2PIM transformation logic using the defined rules.
│   ├── PIM2PSM               # Directory defining the 8 transformation rules and logic for PIM to PSM.
│   │   └── pim2psm.py        # Implements the PIM2PSM transformation logic using the defined rules.
│
├── TransformationResults
│   ├── Classes               # Stores CSV files that contain details of imported and generated classes at each transformation step.
│   ├── Relations             # Stores CSV files that contain details of imported and generated relations at each transformation step.
│
├── requirements.txt          # Lists all Python dependencies required for executing the tool.
├── main.py                   # Main entry point to execute the MoDT-M2M-TT tool.
└── README.md                 # Comprehensive documentation for understanding and using the repository.
```

## MoDT-M2M-TT Tool Execution
The *MoDT-M2M-TT* tool is executed by running the `main.py` script. It can be run via the command line or any IDE 
that supports Python execution. 

### Prerequisites 
Before running `main.py`, a Python Virtual Environment must be activated. The environment can be created using the 
provided **requirements.txt** file. 

Moreover, to properly execute the *MoDT-M2M-TT* tool, the starting domain model (the CIM) must be exported in XML 
format and placed in the following directory:

> *path/to/repository/MoDT-M2M-TT/MDAModelinLevels/01.CIM/VP_GENERATED_XML*

If the directory path is modified, the constant **CIM_VP_XML_FILE_PATH**, located in [**constants.py**](TransformationRules/constants.py), 
must be updated accordingly. 

For ensuring replicability, an existing UML class diagram representing the *Bologna Mobility Domain Model* is already 
available in XML format.

### Setup Instructions for Execution from Command Line
1. Clone the repository to your local machine:
     ```bash
   git clone repository-url
2. Navigate to the repository directory
    ```bash
   cd /path/to/repository
3. Create and activate a virtual environment
   1. If virtualenv is not installed in your local machine, install it by running:
   ```bash
   python3 -m pip install virtualenv
   ```
   2. Create a Python virtual environment:
   ```bash
   virtualenv venv
   ```
   3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
4. Once the Python virtual environment has been created and activated, install the required Python packages using 
   the **requirements.txt**:
    ```bash
   pip3 install -r requirements.txt
   ```
5. Run the `main.py` script:
   ```bash
   python3 main.py
   ```

### Setup Instructions for Execution from IDE
1. Open the project in your preferred IDE (e.g., PyCharm, VSCode, etc.).
2. Ensure the Python interpreter for the project is set to the virtual environment created in the setup process 
   and that the required packages are installed.
3. Run the `main.py` script within the IDE.


## Execution Results

The execution of the `main.py` script will generate the following outputs:

1. **Imported CIM Classes and Relations**  
   The tool extracts the set of CIM classes and relations from the XML representing the CIM imported from Visual Paradigm. These are saved in:  
   - [*imported_cimclasses.csv*](TransformationResults/Classes/imported_cimclasses.csv): Contains the imported CIM classes.  
   - [*imported_cimrelations.csv*](TransformationResults/Relations/imported_cimrelations.csv): Contains the imported CIM relations.  

2. **Generated PIM Classes and Relations**  
   The tool applies **CIM2PIM transformations** to generate PIM classes and relations. These results are saved as:  
   - [*pim.xml*](MDAModelinLevels/02.PIM/M2MT_GENERATED_XML/pim.xml): The generated PIM model in XML format.  
   - [*generated_pimclasses.csv*](TransformationResults/Classes/generated_pimclasses.csv): Contains the generated PIM classes.  
   - [*generated_pimrelations.csv*](TransformationResults/Relations/generated_pimrelations.csv): Contains the generated PIM relations.  

   The resulting classes and relations can either be sent to the next transformation process or the XML can be imported into Visual Paradigm for visualizing the resulting class diagram.

3. **Generated PSM Classes and Relations**  
   The tool applies **PIM2PSM transformations** to generate PSM classes and relations. These results are saved as:  
   - [*psm.xml*](MDAModelinLevels/03.PSM/M2MT_GENERATED_XML/psm.xml): The generated PSM model in XML format.  
   - [*generated_psmclasses.csv*](TransformationResults/Classes/generated_psmclasses.csv): Contains the generated PSM classes.  
   - [*generated_psmrelations.csv*](TransformationResults/Relations/generated_psmrelations.csv): Contains the generated PSM relations.  

   The resulting classes and relations can be imported into Visual Paradigm or any modeling tool that supports Model-to-Text transformations using Python as the programming language.

4. **Software Code Artifacts (ISM)**  
   The final set of software code artifacts is stored in the [*04.ISM*](MDAModelinLevels/04.ISM) folder. These Python modules are automatically generated through Model-To-Text (M2T) transformations.  
   > **Note**: The M2T transformation process is external to the MoDT-M2M-TT tool and is included for the sake of completeness.



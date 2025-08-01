import pymupdf4llm
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from schemas.user_data import UserData
import logging
import re
import json
from pydantic import create_model
from typing import Optional


logger = logging.getLogger(__name__)

def get_pdf_markdown(pdf_path: str) -> str:
    """Converts a PDF file to markdown format."""
    print("Converting PDF to Markdown...")
    markdown_text = pymupdf4llm.to_markdown(pdf_path)
    print("PDF conversion complete.")
    return markdown_text

def clean_value(value: str) -> str:
    """
    Cleans up extracted string values by removing noise and extra whitespace.
    Returns 'N/A' if the value is empty after cleaning.
    """
    if not value:
        return "N/A"
    # Replace <br> tags and newlines with spaces
    cleaned = re.sub(r'<br\s*/?>|\n', ' ', value, flags=re.IGNORECASE)
    # Remove sequences of dots (2 or more), ellipses, and pipe characters
    cleaned = re.sub(r'\.{2,}|…|\|', ' ', cleaned)
    # Remove leading/trailing colons and other noise, then strip whitespace
    cleaned = cleaned.strip(':*_ ').strip()
    # Collapse multiple spaces into one
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else "N/A"


def extract_with_regex(text: str) -> dict:
    """Extracts structured data using regular expressions."""
    print("Phase 1: Extracting data with Regex...")
    data = {}
    
    # --- More robust Key-Value Extractions using lookaheads ---
    simple_fields = {
        # This pattern is specifically designed to capture the multi-line name and stop before "Email:"
        "Nom et Prénom": r"Nom et Prénom\s*:\s*([\s\S]*?)(?=Email\s*:)",
        "Email": r"Email\s*:\s*([\s\S]*?)(?=Fonction:)",
        "Fonction": r"Fonction\s*:\s*([\s\S]*?)(?=Responsable hiérarchique:)",
        # This pattern stops at the pipe character, which separates the table columns
        "Responsable Hiérarchique": r"Responsable hiérarchique\s*:\s*([\s\S]*?)(?=\|)",
        "Matricule": r"Matricule\s*:\s*([\s\S]*?)(?=Entité N:)",
        "Entité N": r"Entité N\s*:\s*([\s\S]*?)(?=Entité N\+2:)",
        "Entité N+2": r"Entité N\+2\s*:\s*([\s\S]*?)(?=\|)", # Ends at the table cell separator
        
        # Fields outside the table
        "Source de données": r"à préciser\s*:\s*([\s\S]*?)(?=Données / Indicateurs / Familles)",
        "Périmètre de données": r"Décrire le périmètre de données\s*\(.*?\)\s*([\s\S]*?)(?=Le périmètre de données demandé)",
        "Famille de données": r"piloter / manipuler\s*:\s*([\s\S]*?)(?=Décrire le périmètre de données)",
        "Finalité de besoin": r"demande d’accès\s*:\s*([\s\S]*?)(?=Commentaires et informations complémentaires)",
        "Commentaires": r"Commentaires et informations complémentaires\s*:\s*([\s\S]*?)(?=A quel système souhaitez-vous avoir accès)",
        "Profil à affecter": r"Profil ou layer\(s\) à affecter.*?Fonctionnelle\)\s*([\s\S]*?)(?=4\.)"
    }

    for field, pattern in simple_fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Use the new, more robust cleaning function
            data[field] = clean_value(match.group(1))
        else:
            # If a field isn't found, set it to 'N/A'
            data[field] = "N/A"

    # --- Checkbox Extractions ---
    checkbox_fields = {
        "Données personnelles": r"données à caractère personnel .*?\n\s*(Oui:\s*[☑☒]|Non:\s*[☑☐])",
        "Données Anonymisées": r"doivent-elles être anonymisées\s*\?\s*(Oui:\s*[☑☒]|Non:\s*[☑☐])",
        "Formation Business Object": r"Formation Business Object\s*:\s*.*? (Oui:\s*[☑☒]|Non:\s*[☑☐])",
        "Formation QlikView": r"Formation QlikView\s*:\s*.*? (Oui:\s*[☑☒]|Non:\s*[☑☐])",
        "Formation SQL": r"Formation SQL\s*:\s*.*? (Oui:\s*[☑☒]|Non:\s*[☑☐])"
    }

    for field, pattern in checkbox_fields.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1)
            # This logic assumes one of the boxes will be checked.
            data[field] = "Oui" if '☑' in value or '☒' in value else "Non"
        else:
            data[field] = "N/A"

    # --- System Access Checkboxes ---
    systemes = re.findall(r"(Borj-Pilotage|QlikView|QlikSense|DataLake|IBM DataStage):\s*[☑☒]", text, re.IGNORECASE)
    data["Accès Système"] = systemes
    
    print(f"Regex extracted {len(data)} fields.")
    return data

def extract_with_llm(text: str, remaining_fields: list) -> dict:
    """Extracts remaining complex data using the LLM."""
    print("Phase 2: Extracting complex data with LLM...")
    
    # If there's nothing for the LLM to do, return early.
    if not remaining_fields:
        print("No remaining fields for LLM to process.")
        return {}
        
    print(f"Asking LLM to find: {remaining_fields}")

    llm = ChatOllama(model="mistral:7b-instruct", format="json", base_url="http://localhost:11434")
    
    # --- Corrected dynamic model creation for Pydantic v2 ---
    dynamic_fields = {
        field_name: (Optional[field_info.annotation], None)
        for field_name, field_info in UserData.__fields__.items() if field_name in remaining_fields
    }
    if not dynamic_fields:
        print("Could not create dynamic model, no valid fields found.")
        return {}
        
    PartialUserData = create_model('PartialUserData', **dynamic_fields)

    parser = JsonOutputParser(pydantic_object=PartialUserData)

    prompt_template = """
    Vous êtes un assistant IA expert en analyse de formulaires. Le texte suivant est un extrait d'un document.
    Votre unique tâche est d'extraire les informations correspondant aux champs demandés dans le schéma JSON.

    **Instructions Clés :**
    1.  **Finalité et Commentaires :** Lisez les sections correspondantes et extrayez le texte descriptif.
    2.  **Signatures :** Pour chaque champ "Signature...", si vous voyez une signature manuscrite, une date, ou toute marque dans la zone de signature correspondante, la valeur doit être "Présente". Si la zone est vide, la valeur doit être "Absente".
    3.  **Profil à affecter :** Extrayez le texte de la section "Profil ou layer(s) à affecter".

    **Schéma JSON à respecter :**
    {format_instructions}

    **Contenu du document à analyser :**
    ---
    {document_content}
    ---
    """

    prompt = ChatPromptTemplate.from_template(
        template=prompt_template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    print("\nSending request to Ollama...")
    response = chain.invoke({"document_content": text})
    print("Ollama has responded.")
    return response


def extract_data_from_pdf(pdf_path: str) -> dict:
    """Extracts data from a PDF using a hybrid regex and LLM approach."""
    markdown_content = get_pdf_markdown(pdf_path)
    
    # --- Ignore the preamble section ---
    content_start_marker = r"\*\*2\.\*\*\s*\*\*Contenu du formulaire\*\*"
    match = re.search(content_start_marker, markdown_content, re.IGNORECASE)
    if match:
        print("Preamble found. Processing content from '2. Contenu du formulaire'.")
        markdown_content = markdown_content[match.end():]
    else:
        print("Preamble marker not found. Processing the whole document.")
    # --- End of preamble ignoring logic ---

    # --- ADDED FOR DEBUGGING ---
    print("\n" + "="*20 + " GENERATED MARKDOWN (AFTER PREAMBLE REMOVAL) " + "="*20)
    print(markdown_content)
    print("="*20 + " END OF MARKDOWN " + "="*51 + "\n")
    # --- END OF DEBUGGING ADDITION ---

    # --- Step 1: Extract what we can with Regex ---
    final_data = extract_with_regex(markdown_content)

    # --- Step 2: Determine which fields are still missing or were not found by regex ---
    all_fields_map = {v.alias: k for k, v in UserData.__fields__.items()}
    missing_fields = []
    for alias, field_name in all_fields_map.items():
        if final_data.get(alias) == "N/A":
            missing_fields.append(field_name)

    llm_data = {}
    if missing_fields:
        # --- Step 3: Use LLM to find the remaining fields ---
        llm_data = extract_with_llm(markdown_content, missing_fields)
    else:
        print("All data extraccted with Regex. Skipping LLM.")

    # --- Step 4: Merge the results ---
    # The Pydantic alias is the key in the regex_data dict, so we need to map it back to the field name
    alias_to_field_map = {v.alias: k for k, v in UserData.__fields__.items() if v.alias}
    
    # Use the initial regex data as the base
    merged_data = {}
    for alias, value in final_data.items():
        field_name = alias_to_field_map.get(alias, alias)
        merged_data[field_name] = value

    # Add the LLM data, overwriting "N/A" values if the LLM found something
    if llm_data:
        for field_name, value in llm_data.items():
            if value and value != "N/A": # Only update if the LLM returned a non-empty value
                merged_data[field_name] = value

    # Ensure all fields from the schema are present, defaulting to "N/A"
    for field in UserData.__fields__:
        if field not in merged_data:
            merged_data[field] = "N/A"
    
    # Use the Pydantic model to validate and serialize the final data
    validated_data = UserData(**merged_data)
    
    # We return the dict using aliases for the FastAPI endpoint
    return json.loads(validated_data.json(by_alias=True))

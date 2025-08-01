from pydantic import BaseModel, Field
from typing import Optional

class UserData(BaseModel):
    nom_et_prenom: Optional[str] = Field(None, alias="Nom et Prénom")
    email: Optional[str] = Field(None, alias="Email")
    fonction: Optional[str] = Field(None, alias="Fonction")
    responsable_hierarchique: Optional[str] = Field(None, alias="Responsable Hiérarchique")
    matricule: Optional[str] = Field(None, alias="Matricule")
    entite_n: Optional[str] = Field(None, alias="Entité N")
    entite_n_plus_2: Optional[str] = Field(None, alias="Entité N+2")
    acces_systeme: list[str] = Field(default_factory=list, alias="Accès Système")
    commentaires: Optional[str] = Field(None, alias="Commentaires")
    donnees_anonymisees: Optional[str] = Field(None, alias="Données Anonymisées")
    donnees_personnelles: Optional[str] = Field(None, alias="Données personnelles")
    famille_de_donnees: Optional[str] = Field(None, alias="Famille de données")
    finalite_de_besoin: Optional[str] = Field(None, alias="Finalité de besoin")
    formation_business_object: Optional[str] = Field(None, alias="Formation Business Object")
    formation_qlikview: Optional[str] = Field(None, alias="Formation QlikView")
    formation_sql: Optional[str] = Field(None, alias="Formation SQL")
    profil_a_affecter: Optional[str] = Field(None, alias="Profil à affecter")
    perimetre_de_donnees: Optional[str] = Field(None, alias="Périmètre de données")
    source_de_donnees: Optional[str] = Field(None, alias="Source de données")
    signature_dpo: Optional[str] = Field(None, alias="Signature Data Protection Office")
    signature_admin_data_office: Optional[str] = Field(None, alias="Signature Administration Fonctionnelle Data Office")
    signature_etudes_sig: Optional[str] = Field(None, alias="Signature Etudes et développements SIG")
    signature_hierarchie: Optional[str] = Field(None, alias="Signature Hiérarchie")
    signature_demandeur: Optional[str] = Field(None, alias="Signature du demandeur")


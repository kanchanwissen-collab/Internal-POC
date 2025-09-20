from pydantic import BaseModel
from typing import List, Dict, Any, Literal
from .process_type_enum import ProcessType
from .vendor_enum import VendorName
from .batch import ProcedureCode, OtherField, TaskAssignment


# EVICORE request model
class EvicoreRequest(BaseModel):
    vendorname: Literal["Evicore"]
    requestid: str
    appointmentid: str
    appointmentdate: str
    caseid: str
    visittype: str
    authorizationtype: str
    clientspecialty: str
    providerfirstname: str
    providerlastname: str
    providernpi: str
    providershortcode: str = ""
    providerphone: str = ""
    provideraddress1: str
    provideraddress2: str = ""
    providercity: str
    providerstate: str
    providerzip: str
    providercountry: str
    subscriberfirstname: str
    subscriberlastname: str
    subscriberaddress1: str
    subscriberaddress2: str = ""
    subscribercity: str
    subscriberstate: str
    subscriberzip: str
    subscribercountry: str
    subscriberdateofbirth: str
    subscribergender: str
    subscriberrelationship: str
    subscriberrelationshipcode: str
    ediservicecode: str = ""
    patientfirstname: str
    patientlastname: str
    patientdateofbirth: str
    personnumber: str
    patientaddress1: str
    patientaddress2: str = ""
    patientcity: str
    patientstate: str
    patientzip: str
    patientcountry: str
    gender: str
    payername: str
    payerid: str
    policynumber: str
    locationcode: str
    locationname: str 
    locationaddress1: str
    locationaddress2: str = ""
    locationcity: str
    locationstate: str
    locationzip: str
    locationcountry: str
    facilitynpi: str
    providergrouptaxid: str
    placeofservice: str
    mandatorydocuments: str = ""
    additionaldocuments: str = ""
    contactname: str
    contactphone: str
    contactfax: str
    dxcodes: str
    cptcodes: str
    procedurecodes: List[ProcedureCode]
    totalprocedurecodes: int
    category: str
    followupdate: str
    clientname: str
    enterpriseid: str
    enterprisename: str
    subsupportedmedium: str
    encounterid: str = ""
    other: Dict[str, OtherField]
    casereferencenumber: str
    snapshotofauth: str = ""
    authstatus: str = ""
    payerresponsedocument: str = ""
    authid: str = ""
    authstartdate: str = ""
    authenddate: str = ""
    totalnumberofvisit: str
    denialreason: str = ""
    denialresponsenumber: str = ""
    denialdate: str = ""
    effectivedate: str
    questionnaire: Dict[str, Any] = {}
    documents: Dict[str, Any] = {}
    taskassignment: TaskAssignment
    authnotes: str = ""

# COHERE request model (example, similar fields, can be customized)

# Import CohereRequest from its own file
from .cohere_request import CohereRequest

# Union type for requests
from typing import Union
RequestUnion = Union[EvicoreRequest, CohereRequest]

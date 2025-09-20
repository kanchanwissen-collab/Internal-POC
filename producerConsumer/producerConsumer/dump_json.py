"""
Generate the Response[] JSON array for batch submission
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict
from app.models import ResponseItem, ProcedureCode, OtherField, TaskAssignment, TaskAssignmentDocument

# Vendor rotation list
vendors = [
    "EVICORE", "Cohere", "Healthera", "ChangeHealthcare", "Availity",
    "Optum", "Epic", "Athenahealth", "Cerner", "Allscripts"
]

def make_response_item(index: int, vendor: str) -> Dict:
    base_date = datetime(2025, 10, 27, 18, 0, 0)
    appointment_date = base_date + timedelta(days=index)

    item = ResponseItem(
        requestid=f"{4473 + index}",
        appointmentid=f"158231849-{index+1}",
        appointmentdate=appointment_date.isoformat(),
        caseid=f"1234587{3 + index}",
        visittype="Initial" if index % 2 == 0 else "Subsequent",
        authorizationtype="Initial",
        clientspecialty="Radiology" if index % 2 == 0 else "Cardiology",
        providerfirstname=f"PROVIDER{index}",
        providerlastname=f"LAST{index}",
        providernpi=f"{index+1}" * 10,
        provideraddress1=f"ADDRESS {index}",
        providercity="CITY",
        providerstate="NY",
        providerzip=f"105{10+index}",
        providercountry="USA",
        subscriberfirstname=f"SUB{index}",
        subscriberlastname=f"NAME{index}",
        subscriberaddress1=f"SUB ADDRESS {index}",
        subscribercity="CITY",
        subscriberstate="NY",
        subscriberzip="10562",
        subscribercountry="US",
        subscriberdateofbirth="1980-01-01T00:00:00",
        subscribergender="Male",
        subscriberrelationship="Self",
        subscriberrelationshipcode="18",
        patientfirstname=f"PAT{index}",
        patientlastname=f"IENT{index}",
        patientdateofbirth="1980-01-01T00:00:00",
        personnumber=f"XXX-{1111111+index}",
        patientaddress1=f"PATIENT ADDRESS {index}",
        patientcity="CITY",
        patientstate="NY",
        patientzip="10562",
        patientcountry="US",
        gender="Male",
        payername="Generic Payer",
        payerid=f"35000{index}",
        policynumber=f"POLICY-{4473+index}",
        locationcode="NY",
        locationname="FACILITY NAME",
        locationaddress1="FACILITY ADDRESS",
        locationcity="CITY",
        locationstate="NY",
        locationzip="10549",
        locationcountry="USA",
        facilitynpi=f"{index+2}" * 11,
        providergrouptaxid=f"{index+3}" * 10,
        placeofservice="11",
        contactname=f"Contact {index}",
        contactphone="888-868-4102",
        contactfax="469-466-6178",
        dxcodes="E66.9,E78.2",
        cptcodes="71271" if index % 2 == 0 else "93000",
        procedurecodes=[
            ProcedureCode(code="71271" if index % 2 == 0 else "93000", unit="1", modifiercode="", diagnosiscode="")
        ],
        totalprocedurecodes=1,
        category="PA_CMM_Sample",
        followupdate=(appointment_date + timedelta(days=10)).isoformat(),
        clientname="CLIENT NAME",
        enterpriseid=f"ENT-{index}",
        enterprisename="ENTERPRISE NAME",
        vendorname=vendor,
        subsupportedmedium="BROWSER",
        other={
            "other1": OtherField(other_que="Auth Submission Comments", other_ans="Good"),
            "other2": OtherField(other_que="Spoke_To", other_ans=""),
            "other3": OtherField(other_que="Contact Email", other_ans="test@example.com"),
        },
        casereferencenumber=f"case-{index+1}",
        totalnumberofvisit="1",
        effectivedate=appointment_date.isoformat(),
        taskassignment=TaskAssignment(
            document1=TaskAssignmentDocument(name="", assignedto="No")
        ),
        authnotes=""
    )
    return item.dict()

def build_response_array() -> List[Dict]:
    return [make_response_item(i, vendors[i%10]) for i in range(100)]

if __name__ == "__main__":
    response_array = build_response_array()
    
    # Create the batch data structure
    batch_data = {"response": response_array}
    
    # Write to a new JSON file
    output_file = "generated_batch_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated batch data written to: {output_file}")
    print(f"Total records: {len(response_array)}")
    print(f"Vendors included: {list(set(vendors[:len(response_array)]))}")

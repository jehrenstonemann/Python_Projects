import json
from zipfile import ZipFile
import csv
from io import TextIOWrapper

class Applicant:
    def __init__(self, age, race):
        self.age = age
        self.race = set()
        race_lookup = {
            "1": "American Indian or Alaska Native",
            "2": "Asian",
            "3": "Black or African American",
            "4": "Native Hawaiian or Other Pacific Islander",
            "5": "White",
            "21": "Asian Indian",
            "22": "Chinese",
            "23": "Filipino",
            "24": "Japanese",
            "25": "Korean",
            "26": "Vietnamese",
            "27": "Other Asian",
            "41": "Native Hawaiian",
            "42": "Guamanian or Chamorro",
            "43": "Samoan",
            "44": "Other Pacific Islander"
        }
        
        for r in race:
            if r in race_lookup:
                self.race.add(race_lookup[r])
        
    def __repr__(self):
        return f"Applicant('{self.age}', {sorted(self.race)})"
    
    def lower_age(self):
        age_str = self.age.replace('<', '').replace('>', '')
        age_range = age_str.split("-")
        return int(age_range[0])
    
    def __lt__(self,other):
        return self.lower_age() < other.lower_age()
    
class Loan:
    def __init__(self, values):
        self.loan_amount = float(values["loan_amount"]) if (values["loan_amount"] != "NA" and values["loan_amount"] != "Exempt") else -1.0
        self.property_value = float(values["property_value"]) if (values["property_value"] != "NA" and values["property_value"] != "Exempt") else -1.0
        self.interest_rate = float(values["interest_rate"]) if (values["interest_rate"] != "NA" and values["interest_rate"] != "Exempt") else -1.0
        self.applicants = []
        
        age = values["applicant_age"]
        race = [values[f"applicant_race-{i}"] for i in range(1, 6) if values.get(f"applicant_race-{i}")]
        self.applicants.append(Applicant(age, race))
        
        if(values["co-applicant_age"] != "9999"):
            co_age = values["co-applicant_age"]
            co_race = [values[f"co-applicant_race-{i}"] for i in range(1, 6) if values.get(f"co-applicant_race-{i}")]
            self.applicants.append(Applicant(co_age, co_race))
    def __str__(self):
        return f"<Loan: {self.interest_rate}% on ${self.property_value} with {len(self.applicants)} applicant(s)>"
    
    def __repr__(self):
        return str(self)
    
    def yearly_amounts(self, yearly_payment):
        assert self.interest_rate >= 0 and self.loan_amount >= 0
        amt = self.loan_amount
        while amt > 0:
            yield amt
            amt += amt * (self.interest_rate / 100)
            amt -= yearly_payment

class Bank:
    def __init__(self, bankName):
        with open('banks.json', 'r') as file:
            banks_data = json.load(file)
        self.lei = None
        self.loans = []
        for bank in banks_data:
            if bankName == bank["name"]:
                self.lei = bank["lei"]
                break
        if self.lei is None:
            raise ValueError(f"Bank with name '{bankName}' not found in banks.json")\
            
        with ZipFile('wi.zip') as zf:
            with zf.open("wi.csv") as f:
                wi = csv.DictReader(TextIOWrapper(f))
                for loan_info in wi:
                    if loan_info["lei"] == self.lei:
                        loan = Loan(loan_info)
                        self.loans.append(loan)
                        
    def __getitem__(self, index):
        if index >= 0:
            if index >= len(self.loans):
                raise IndexError("Invalid Index")
        else:
            if abs(index) > len(self.loans):
                raise IndexError("Invalid Index")
            index = len(self.loans) + index
        return self.loans[index]
    
    def __len__(self):
        return len(self.loans)
            
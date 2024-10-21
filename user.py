import json

class User:
    def serialize(self):
        return self.__dict__
                
    def set_password(self, hashed):
        self.password = hashed
          
class NormalUser(User):
    
    def __init__(self, kvpairing):
        self.first_name = kvpairing["first_name"]
        self.last_name = kvpairing["last_name"]
        self.middle_name = kvpairing["middle_name"]
        self._id = kvpairing["email"]
        self.phone_number = kvpairing["phone"]
        self.dob = kvpairing["dob"]
        self.job = kvpairing["profession"]
        self.current_service = kvpairing["visa-service"]
        self.gender = kvpairing["gender"]
        self.status = "Not Started"
        
    def change_status(self, status):
        self.status = status   

    def set_rand_id(id):
        self.rand_id = id


class BusinessUser(User):
    
    def __init__(self, kvpairing, from_db = False):
        if not from_db:  
            self.first_name = kvpairing["first_name"]
            self.last_name = kvpairing["last_name"]
            self._id = kvpairing["email"]
            self.clients = [] #store client ids
            self.businessname = kvpairing["business_name"]
        else:
            self.first_name = kvpairing["first_name"]
            self.last_name = kvpairing["last_name"]
            self._id = kvpairing["_id"]
            self.clients = kvpairing["clients"]
            self.businessname = kvpairing["businessname"]
            self.password = kvpairing["password"]
            
        
    def add_client(self, email):
        #we should add this to the client database first
        self.clients.append(email)

    def remove_client(self, email):
        try:
            self.clients.remove(email)
        except ValueError as ve:
            #add logging information here
            #probably do that next week, so we can keep track of operations
            return

        
    def update_business_information(self, kvpairing):
        self.business_type = kvpairing["business_type"]
        self.nclients = kvpairing["nclients"]
        self.country = kvpairing["country"]
        self.visa_spec = kvpairing["visa_spec"]
        self.phone = kvpairing["phone"]
        self.address = kvpairing["address"]
                   
def test_serializer():
    test = {
        "first_name": "Nnanna",
        "last_name": "Omoke",
        "middle_name": None,
        "email": "omokennanna832@gmail.com",
        "phone": "09151999041",
        "dob": "31-5-2006",
        "profession": "student",
        "visa-service": None,
        "gender": "helicopter-helicopter" 
    }
    user = NormalUser(test)
    string = user.serialize()
    print(string)
    print(type(string))

        

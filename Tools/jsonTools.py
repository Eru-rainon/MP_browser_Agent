import json


class JsonTools():
    def loadCredentials(self,path):
        with open(path,"r") as cred:
            creds = json.load(cred)
            return creds
    



    def storetoJson(self, data):
        try:
          
            if isinstance(data, str):
                if data.startswith("'") and data.endswith("'"):
                    data = data[1:-1]
                elif data.startswith("\"") and data.endswith("\""):
                    data = data[1:-1]
                elif data.startswith("'''") and data.endswith("'''"):
                    data = data[3:-3]
                data = json.loads(data)

            json.dumps(data)  

           
            try:
                with open("response.json", "r") as file:
                    existingData = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                existingData = []

            
            if not isinstance(existingData, list):
                existingData = [existingData]

            
            if isinstance(data, list):
                existingData.extend(data)
            else:
                existingData.append(data)


            with open("response.json", "w") as file:
                json.dump(existingData, file, indent=2)

            return "Data appended to response.json"

        except json.JSONDecodeError as e:
            return f"Failed to parse JSON string: {e}"
        except TypeError as e:
            return f"Data is not JSON serializable: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

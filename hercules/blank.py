
class Blank:
    
    def __init__(self, name):
        
        self._name = name
        
    def __call__(self):
        
        print("My name is ", self._name)

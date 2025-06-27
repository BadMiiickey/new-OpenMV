class AssistantHelper:
    
    @staticmethod
    def mapValue(x: float | int, inMin: float | int, inMax: float | int, outMin: float | int, outMax: float | int):
        return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
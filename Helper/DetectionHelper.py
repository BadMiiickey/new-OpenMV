class DetectionHelper:
    detectionMap = {
        (1, 3): "BLACK",
        (2, 1): "RED",
        (3, 2): "YELLOW"
    }
    myCount = 0

    def __init__(self, myCount: int):
        self.detectionMap = DetectionHelper.detectionMap.copy()
        self.countMap = DetectionHelper.myCount
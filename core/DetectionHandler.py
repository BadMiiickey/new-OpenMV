class DetectionHandler:
    detectionMap = {
        (1, 3): "GREEN",
        (2, 1): "RED",
        (3, 2): "YELLOW"
    }
    detectCount = 0

    @staticmethod
    def analyseResult(result: list, currentTarget: int):
        scores = result[0]

        if (len(scores.shape) == 4):
            scores = scores[0]

        maxConfidence = 0
        bestX = 0
        bestY = 0
            
        for (yIndex, yValue) in enumerate(scores):
            for (xIndex, xValue) in enumerate(yValue):
                if(xValue[currentTarget] <= maxConfidence): continue
                
                maxConfidence = max(xValue[currentTarget], maxConfidence)
                bestX = xIndex
                bestY = yIndex

        return (maxConfidence, bestX, bestY)



        
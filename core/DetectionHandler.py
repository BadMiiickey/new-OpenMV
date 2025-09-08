from image import Image # type: ignore

class DetectionHandler:
    detectionMap = {
        1: "GREEN",
        2: "RED",
        3: "YELLOW"
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
                if (xValue[currentTarget] <= maxConfidence): continue
                
                maxConfidence = max(xValue[currentTarget], maxConfidence)
                bestX = xIndex
                bestY = yIndex

        return (scores, maxConfidence, bestX, bestY)

    @staticmethod
    def getMaxBlob(image: Image, scores, gridX: int, gridY: int):
        gridH = scores.shape[-3]
        gridW = scores.shape[-2]

        centerX = int((gridX + 0.5) * image.width() / gridW)
        centerY = int((gridY + 0.5) * image.height() / gridH)
        w = int(image.width() / gridW)
        h = int(image.height() / gridH)
        leftX = centerX - w // 2
        leftY = centerY - h // 2
        pixels = w * h

        return (leftX, leftY, w, h, pixels, centerX, centerY, 0)
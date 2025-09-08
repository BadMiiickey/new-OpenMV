class BlobHandler:

    # 获取像素x
    @staticmethod
    def getX(blob: list[int]):
        return blob[0]
    
    # 获取像素y
    @staticmethod
    def getY(blob: list[int]):
        return blob[1]
    
    # 获取像素width
    @staticmethod
    def getW(blob: list[int]):
        return blob[2]
    
    # 获取像素height
    @staticmethod
    def getH(blob: list[int]):
        return blob[3]
    
    # 获取像素面积
    @staticmethod
    def getPixels(blob: list[int]):
        return blob[4]
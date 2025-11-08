import sensor # type: ignore

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(30) # 等待摄像头稳定跳过的帧数
sensor.set_auto_whitebal(False) # 关闭自动白平衡
sensor.set_auto_gain(False) # 关闭自动增益
sensor.set_auto_exposure(False, exposure_us=6000) # 关闭自动曝光, 设置曝光时间

while (True):
    image = sensor.snapshot()

    roiWidth: int = 10
    roiHeight: int = 10
    roiCenterX: int = (image.width() - roiWidth) // 2
    roiCenterY: int = (image.height() - roiHeight) // 2

    roi: tuple[int, int, int, int] = (roiCenterX, roiCenterY, roiWidth, roiHeight)
    roiStatistics = image.get_statistics(roi=roi)

    lMin: int = roiStatistics.l_min()
    lMax: int = roiStatistics.l_max()
    aMin: int = roiStatistics.a_min()
    aMax: int = roiStatistics.a_max()
    bMin: int = roiStatistics.b_min()
    bMax: int = roiStatistics.b_max()

    threshold = (lMin, lMax, aMin, aMax, bMin, bMax)

    image.binary([threshold])
    image.draw_rectangle(roi, color=(255, 0, 0))

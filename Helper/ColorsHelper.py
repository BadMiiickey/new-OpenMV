class ColorsHelper:
    circleColors: list[tuple[int, int, int]] = [
        (255,   0,   0),
        (  0, 255,   0),
        (255, 255,   0),
        (  0,   0, 255),
        (255,   0, 255),
        (  0, 255, 255),
        (255, 255, 255)
    ]

    # redThreshold = (13, 45, 20, 57, -3, 22)
    # yellowThreshold = (50, 89, -5, 11, 40, 69)
    # blackThreshold = (0, 26, -23, 8, -24, 2)
    sizeThreshold = 10000
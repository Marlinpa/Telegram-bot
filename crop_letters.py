import cv2
import numpy as np
import os
import json

import imutils
from imutils.contours import sort_contours


def overlay_transparent(background_img, img_to_overlay_t, x, y):
    bg_img = background_img.copy()

    b, g, r, a = cv2.split(img_to_overlay_t)
    overlay_color = cv2.merge((b, g, r))

    # маска в которой активны только непрозрачные пиксели
    mask = cv2.medianBlur(a, 1)

    # размеры буквы
    h, w, _ = overlay_color.shape

    # берем кусочек background, который должен находиться под буквой
    roi = bg_img[y:y + h, x:x + w]

    # берем с помощью отрицания от маски из фона те куски, которые не попадают в букву
    img1_bg = cv2.bitwise_and(roi.copy(), roi.copy(), mask=cv2.bitwise_not(mask))

    # берем из буквы те пиксели, что были непрозрачными, то есть были частью буквы
    img2_fg = cv2.bitwise_and(overlay_color, overlay_color, mask=mask)

    # совмещаем новый фон для буквы и букву и заменяем соответствующую области на background
    bg_img[y:y + h, x:x + w] = cv2.add(img1_bg, img2_fg)

    return bg_img


def make_transparent(src):
    tmp = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

    # добавляем черным пикселям полную прозрачность в альфа канале
    _, alpha = cv2.threshold(tmp, 0, 255, cv2.THRESH_BINARY)
    b, g, r = cv2.split(src)

    # добавляем альфа-канал к RGB и получаем RGBA, где любой черный пиксель исходного изображения - прозрачный
    rgba = [b, g, r, alpha]
    dst = cv2.merge(rgba, 4)
    return dst


def remove_background(img):
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lower = 0
    upper = 130

    # оставляем только достаточно темные пиксели lower <= pixel <= upper
    thresh = cv2.inRange(grey, lower, upper)
    # cv2.imshow("thresh", thresh)
    # cv2.waitKey(0)

    # все, что не попало в thresh, то есть было слишком светлым превращаем в черные пиксели
    # так как make_transparent умеет удалять только черный фон
    result = cv2.bitwise_and(img, img, mask=thresh)
    return make_transparent(result)


def find_letters(user_id: int):
    path = os.path.join('pictures', f'{user_id}.jpg')
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # используем алгоритм Кэнни для выделения границ букв
    edged = cv2.Canny(blurred, 30, 250)

    # описываем около каждой границы прямоугольник
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sort_contours(cnts, method="left-to-right")[0]

    black = np.zeros(image.shape, dtype=np.uint8)
    black = cv2.cvtColor(black, cv2.COLOR_BGR2GRAY)

    # все пересекающиеся прямоугольники считаем принадлежащими одной букве
    # составляем маску из черного изображения, где белым выделены прямоугольники найденные выше
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        # cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), 3)
        points = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ])
        cv2.fillPoly(black, [points], (255, 255, 255))
    # cv2.imshow("image", image)
    # cv2.imshow("black", black)
    # cv2.waitKey(0)

    # для каждой группы прямоугольников принадлежащих одной букве ищем границы наименьшего прямоуголтнрика их
    # содержащего, полученный прямоугольник будет содержать в себе букву
    letters_cnt, _ = cv2.findContours(black, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    letters_cnt = sort_contours(letters_cnt, method="left-to-right")[0]
    width = {}
    height = {}

    letters_folder = os.path.join('letters', f'{user_id}')
    if not os.path.isdir(letters_folder):
        os.mkdir(letters_folder)

    # вырезаем буквы и из каждой буквы удаляем фон, делая его прозрачным,
    # сохраняем результат в png
    for i, c in enumerate(letters_cnt):
        x, y, w, h = cv2.boundingRect(c)
        # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 3)
        crop_img = image[y:y + h, x:x + w]
        width[i] = w
        height[i] = h
        letter = remove_background(crop_img)

        cv2.imwrite(os.path.join(letters_folder, f"{i}.png"), letter)
    with open(os.path.join(letters_folder, "stats.json"), 'w') as f:
        json.dump(
            {
                'width': width,
                'height': height
            },
            fp=f
        )


    # cv2.imwrite("parts.jpg", image)
#
#
# d = cv2.imread(r"letters\4.png", -1)
# a = cv2.imread(r"letters\0.png", -1)
# background = cv2.imread(r'C:\Users\Leastick\PycharmProjects\pythonProject\filler_cv\remove_background\back.jpg')
#
# print(background.shape, d.shape)
#
# img = overlay_transparent(background, d, 0, 0)
# img = overlay_transparent(img, a, 80, 0)
# img = overlay_transparent(img, a, 180, 0)
# img = overlay_transparent(img, a, 300, 0)
# img = overlay_transparent(img, a, 420, 0)
#
# cv2.imshow("img", img)
# cv2.waitKey(0)
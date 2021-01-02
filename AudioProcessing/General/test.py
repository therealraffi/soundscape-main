ignore = 120
angles = [[288.2106840638463, 1], [168.3565152243961, 2], [255.48778514717512, 3]]
motors = [0] * 6
inc = (360 - ignore) / 5
analysis = []

possible = [(180 + ignore)/2 + i * inc for i in range(5)]
possible.insert(0, (180 - ignore)/2)

print(motors, possible, angles)
for angle, channel in angles:
    ind = 0
    print(angle, channel)
    for c, k in enumerate(possible):
        if k - inc/2 <= angle <= k + inc/2:
            ind = c
            if motors[ind] != 0:
                if ind == 5:
                    if motors[0] == 0:
                        ind = 0
                        break
                    if motors[4] == 0:
                        ind = 4
                        break
                else:
                    if motors[ind + 1] == 0:
                        ind += 1
                        break
                    if motors[ind - 1] == 0:
                        ind -= 1
                        break
            else:
                break
    motors[ind] = [max(analysis[channel][0] * 80/100, 0), analysis[channel][1]] if analysis[channel][0] > 3 else 0